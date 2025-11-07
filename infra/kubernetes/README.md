# Kubernetes Deployment Guide

## Overview

This directory contains Kubernetes manifests for deploying the Intellium Patent Guard backend to a Kubernetes cluster with production-ready configuration.

## Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` configured and connected to your cluster
- NGINX Ingress Controller installed
- cert-manager installed (for TLS certificates)
- Docker image built and pushed: `intellium/backend:latest`

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Ingress (TLS)                 │
│  api.intellium.example.com                      │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│            Backend Service (ClusterIP)          │
│                  Port 8000                      │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│         Backend Deployment (3-10 pods)          │
│              HPA enabled                        │
└──────┬──────────────────────────────────┬───────┘
       │                                  │
       ▼                                  ▼
┌──────────────────┐            ┌──────────────────┐
│  PostgreSQL      │            │     Redis        │
│  StatefulSet     │            │   Deployment     │
│  (Persistent)    │            │  (Persistent)    │
└──────────────────┘            └──────────────────┘

┌─────────────────────────────────────────────────┐
│       Celery Workers (2-8 pods)                 │
│              HPA enabled                        │
└─────────────────────────────────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `namespace.yaml` | Namespace definition |
| `configmap.yaml` | Application configuration (non-sensitive) |
| `secrets.yaml` | Sensitive credentials (base64 encoded) |
| `postgres.yaml` | PostgreSQL StatefulSet + Service |
| `redis.yaml` | Redis Deployment + PVC + Service |
| `backend.yaml` | Backend Deployment + Service |
| `celery-worker.yaml` | Celery worker Deployment |
| `ingress.yaml` | Ingress with TLS + cert-manager |
| `hpa.yaml` | Horizontal Pod Autoscalers |
| `network-policy.yaml` | Network security policies |
| `deploy.sh` | Automated deployment script |

## Quick Start

### 1. Build and Push Docker Image

```bash
cd backend
docker build -t intellium/backend:latest .
docker push intellium/backend:latest
```

### 2. Update Secrets

Edit `secrets.yaml` and update with your base64-encoded values:

```bash
# Example: Encode a value
echo -n 'your-secret-value' | base64

# Update these secrets:
# - DATABASE_PASSWORD
# - SECRET_KEY (min 32 characters)
# - MINIO_ACCESS_KEY / MINIO_SECRET_KEY
# - STRIPE_SECRET_KEY / STRIPE_WEBHOOK_SECRET
# - FIRST_SUPERUSER_PASSWORD
```

### 3. Update ConfigMap

Edit `configmap.yaml`:
- Update `CORS_ORIGINS` with your domains
- Adjust resource limits if needed
- Update MinIO/external service endpoints

### 4. Update Ingress

Edit `ingress.yaml`:
- Replace `intellium.example.com` with your domain
- Update email in ClusterIssuer for Let's Encrypt

### 5. Deploy

```bash
cd infra/kubernetes
./deploy.sh
```

Or manually:

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Apply configs and secrets
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml

# Deploy databases
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml

# Wait for databases
kubectl wait --for=condition=ready pod -l app=postgres -n intellium --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n intellium --timeout=300s

# Deploy backend
kubectl apply -f backend.yaml
kubectl apply -f celery-worker.yaml

# Deploy autoscaling
kubectl apply -f hpa.yaml

# Deploy network policies
kubectl apply -f network-policy.yaml

# Deploy ingress (requires nginx-ingress + cert-manager)
kubectl apply -f ingress.yaml
```

## Configuration

### Environment Variables

**ConfigMap (non-sensitive):**
- Application settings (ENVIRONMENT, DEBUG, LOG_LEVEL)
- Database connection details (host, port, name)
- Redis connection details
- CORS origins
- API configuration

**Secrets (sensitive, base64-encoded):**
- Database credentials
- JWT secret key
- MinIO credentials
- Stripe API keys
- Admin user credentials

### Resource Limits

**Backend:**
- Requests: 512Mi RAM, 500m CPU
- Limits: 1Gi RAM, 1000m CPU
- Replicas: 3-10 (HPA)

**Celery Workers:**
- Requests: 512Mi RAM, 500m CPU
- Limits: 1Gi RAM, 1000m CPU
- Replicas: 2-8 (HPA)

**PostgreSQL:**
- Requests: 256Mi RAM, 250m CPU
- Limits: 512Mi RAM, 500m CPU
- Storage: 10Gi

**Redis:**
- Requests: 128Mi RAM, 100m CPU
- Limits: 256Mi RAM, 200m CPU
- Storage: 5Gi

### Autoscaling

**Backend HPA:**
- Min replicas: 3
- Max replicas: 10
- CPU threshold: 70%
- Memory threshold: 80%

**Celery HPA:**
- Min replicas: 2
- Max replicas: 8
- CPU threshold: 75%
- Memory threshold: 85%

## TLS Certificates

### Prerequisites

Install cert-manager:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### Configuration

The `ingress.yaml` includes:
- `ClusterIssuer` for Let's Encrypt production
- `Certificate` resource for automatic issuance
- TLS configuration in Ingress

Certificates are automatically issued and renewed.

### Check Certificate Status

```bash
kubectl get certificate -n intellium
kubectl describe certificate intellium-tls -n intellium
```

## Networking

### Services

- **backend-service**: ClusterIP, port 8000
- **postgres-service**: Headless (ClusterIP: None) for StatefulSet
- **redis-service**: ClusterIP, port 6379

### Ingress

- **Host**: `api.intellium.example.com`
- **TLS**: Automatic via cert-manager
- **Rate limiting**: 100 requests/second
- **CORS**: Configured for allowed origins
- **Max body size**: 50MB

### Network Policies

Security policies restrict traffic:
- Backend can access PostgreSQL and Redis
- PostgreSQL accepts connections only from backend/workers
- Redis accepts connections only from backend/workers
- All pods can do DNS lookups
- Backend can make external HTTPS calls

## Monitoring

### Health Checks

**Liveness Probes:**
- Backend: `GET /health` (30s initial delay)
- PostgreSQL: `pg_isready` command
- Redis: TCP socket check

**Readiness Probes:**
- Backend: `GET /health` (10s initial delay)
- PostgreSQL: `pg_isready` command
- Redis: `redis-cli ping`

### Metrics

Backend pods are annotated for Prometheus scraping:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

## Common Operations

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n intellium

# Celery worker logs
kubectl logs -f deployment/celery-worker -n intellium

# PostgreSQL logs
kubectl logs -f statefulset/postgres -n intellium

# Redis logs
kubectl logs -f deployment/redis -n intellium
```

### Scale Deployments

```bash
# Manual scaling
kubectl scale deployment/backend --replicas=5 -n intellium
kubectl scale deployment/celery-worker --replicas=4 -n intellium

# Check HPA status
kubectl get hpa -n intellium
kubectl describe hpa backend-hpa -n intellium
```

### Database Operations

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n intellium -- psql -U postgres -d intellium_db

# Run migrations
kubectl exec -it deployment/backend -n intellium -- alembic upgrade head

# Backup database
kubectl exec postgres-0 -n intellium -- pg_dump -U postgres intellium_db > backup.sql

# Restore database
cat backup.sql | kubectl exec -i postgres-0 -n intellium -- psql -U postgres -d intellium_db
```

### Redis Operations

```bash
# Connect to Redis
kubectl exec -it deployment/redis -n intellium -- redis-cli

# Flush cache
kubectl exec deployment/redis -n intellium -- redis-cli FLUSHALL
```

### Port Forwarding

```bash
# Access backend locally
kubectl port-forward svc/backend-service 8000:8000 -n intellium
# Open: http://localhost:8000/docs

# Access PostgreSQL locally
kubectl port-forward svc/postgres-service 5432:5432 -n intellium

# Access Redis locally
kubectl port-forward svc/redis-service 6379:6379 -n intellium
```

### Rolling Updates

```bash
# Update backend image
kubectl set image deployment/backend backend=intellium/backend:v2.0.0 -n intellium

# Check rollout status
kubectl rollout status deployment/backend -n intellium

# Rollback if needed
kubectl rollout undo deployment/backend -n intellium

# View rollout history
kubectl rollout history deployment/backend -n intellium
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n intellium

# Describe pod for events
kubectl describe pod <pod-name> -n intellium

# Check logs
kubectl logs <pod-name> -n intellium

# Check init container logs
kubectl logs <pod-name> -c wait-for-db -n intellium
kubectl logs <pod-name> -c migrate -n intellium
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
kubectl exec -it deployment/backend -n intellium -- nc -zv postgres-service 5432

# Check PostgreSQL logs
kubectl logs statefulset/postgres -n intellium

# Verify secrets
kubectl get secret intellium-secrets -n intellium -o yaml
```

### Certificate Issues

```bash
# Check certificate status
kubectl get certificate -n intellium
kubectl describe certificate intellium-tls -n intellium

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Manual certificate renewal
kubectl delete certificate intellium-tls -n intellium
kubectl apply -f ingress.yaml
```

### Ingress Not Working

```bash
# Check ingress status
kubectl get ingress -n intellium
kubectl describe ingress intellium-ingress -n intellium

# Check nginx-ingress logs
kubectl logs -n ingress-nginx deployment/nginx-ingress-controller

# Get ingress IP
kubectl get ingress intellium-ingress -n intellium -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

## Security Best Practices

1. **Secrets Management:**
   - Use external secret managers (AWS Secrets Manager, HashiCorp Vault)
   - Rotate secrets regularly
   - Never commit actual secrets to git

2. **Network Policies:**
   - Keep network policies restrictive
   - Review and update policies regularly
   - Use namespaces for isolation

3. **Resource Limits:**
   - Always set resource requests and limits
   - Monitor actual usage and adjust
   - Use LimitRanges for namespace defaults

4. **RBAC:**
   - Use service accounts with minimal permissions
   - Avoid using default service account
   - Regular RBAC audits

5. **Image Security:**
   - Use specific image tags (not `latest`)
   - Scan images for vulnerabilities
   - Use private registries

## Cleanup

```bash
# Delete everything
kubectl delete namespace intellium

# Or delete individual resources
kubectl delete -f ingress.yaml
kubectl delete -f hpa.yaml
kubectl delete -f celery-worker.yaml
kubectl delete -f backend.yaml
kubectl delete -f redis.yaml
kubectl delete -f postgres.yaml
kubectl delete -f secrets.yaml
kubectl delete -f configmap.yaml
kubectl delete -f namespace.yaml
```

## Production Checklist

- [ ] Update all secrets with strong, unique values
- [ ] Replace example domains with actual domains
- [ ] Configure DNS records to point to Ingress IP
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log aggregation (ELK, Loki, etc.)
- [ ] Set up backup strategy for PostgreSQL
- [ ] Configure alerts for critical metrics
- [ ] Review and test disaster recovery plan
- [ ] Enable pod security policies
- [ ] Set up CI/CD pipeline for automated deployments
- [ ] Configure resource quotas for namespace
- [ ] Set up external secret management
- [ ] Review network policies
- [ ] Test autoscaling behavior
- [ ] Configure persistent volume snapshots

## Support

For issues or questions:
- Check pod logs: `kubectl logs <pod-name> -n intellium`
- Check events: `kubectl get events -n intellium --sort-by='.lastTimestamp'`
- Describe resources: `kubectl describe <resource-type> <name> -n intellium`
