# Kubernetes Deployment - Quick Reference

## 📦 Files Created (11 manifests)

```
infra/kubernetes/
├── namespace.yaml           # Namespace: intellium
├── configmap.yaml          # Non-sensitive config (35+ vars)
├── secrets.yaml            # Sensitive data (base64 encoded)
├── postgres.yaml           # StatefulSet + Service (10Gi storage)
├── redis.yaml              # Deployment + PVC + Service (5Gi)
├── backend.yaml            # Deployment + Service (3-10 pods)
├── celery-worker.yaml      # Deployment (2-8 pods)
├── ingress.yaml            # Ingress + TLS + cert-manager
├── hpa.yaml                # Horizontal Pod Autoscalers
├── network-policy.yaml     # Security policies
├── deploy.sh               # Automated deployment
└── README.md               # Complete documentation
```

## 🚀 Quick Deploy

```bash
cd infra/kubernetes

# 1. Update secrets (REQUIRED)
nano secrets.yaml  # Replace base64 values

# 2. Update domains (REQUIRED)
nano ingress.yaml  # Replace intellium.example.com
nano configmap.yaml  # Update CORS_ORIGINS

# 3. Deploy everything
./deploy.sh

# Or manually:
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f backend.yaml
kubectl apply -f celery-worker.yaml
kubectl apply -f hpa.yaml
kubectl apply -f network-policy.yaml
kubectl apply -f ingress.yaml
```

## 🔑 Update Secrets (Base64 Encode)

```bash
# Encode values
echo -n 'your-secret-key-min-32-chars' | base64
echo -n 'your-db-password' | base64
echo -n 'sk_live_stripe_key' | base64

# Update these in secrets.yaml:
# - SECRET_KEY
# - DATABASE_PASSWORD
# - STRIPE_SECRET_KEY
# - STRIPE_WEBHOOK_SECRET
```

## 📊 Resource Summary

| Component | Replicas | CPU | Memory | Storage |
|-----------|----------|-----|---------|---------|
| Backend | 3-10 (HPA) | 500m-1000m | 512Mi-1Gi | - |
| Celery | 2-8 (HPA) | 500m-1000m | 512Mi-1Gi | - |
| PostgreSQL | 1 | 250m-500m | 256Mi-512Mi | 10Gi |
| Redis | 1 | 100m-200m | 128Mi-256Mi | 5Gi |

## 🌐 Ingress Configuration

**Domains:** (update in `ingress.yaml`)
- `api.intellium.example.com` → Backend Service
- `admin.intellium.example.com` → Backend Service
- `intellium.example.com` → Backend Service

**Features:**
- ✅ TLS with Let's Encrypt (automatic)
- ✅ Force HTTPS redirect
- ✅ CORS enabled
- ✅ Rate limiting (100 req/s)
- ✅ Max body size: 50MB
- ✅ Timeouts: 60s

## 🔒 Security Features

**Network Policies:**
- Backend → PostgreSQL, Redis only
- PostgreSQL ← Backend, Celery only
- Redis ← Backend, Celery only
- All → DNS resolution
- Backend → External HTTPS

**Secrets:**
- Database credentials
- JWT secret key
- MinIO credentials
- Stripe API keys
- Admin credentials

## 📈 Autoscaling (HPA)

**Backend:**
- Min: 3 pods
- Max: 10 pods
- Triggers: CPU 70%, Memory 80%

**Celery:**
- Min: 2 pods
- Max: 8 pods
- Triggers: CPU 75%, Memory 85%

## 🛠️ Common Commands

```bash
# Check status
kubectl get all -n intellium
kubectl get pods -n intellium -w

# View logs
kubectl logs -f deployment/backend -n intellium
kubectl logs -f deployment/celery-worker -n intellium

# Port forward (local access)
kubectl port-forward svc/backend-service 8000:8000 -n intellium
# Open: http://localhost:8000/docs

# Scale manually
kubectl scale deployment/backend --replicas=5 -n intellium

# Check HPA
kubectl get hpa -n intellium
kubectl describe hpa backend-hpa -n intellium

# Check certificates
kubectl get certificate -n intellium
kubectl describe certificate intellium-tls -n intellium

# Database operations
kubectl exec -it postgres-0 -n intellium -- psql -U postgres -d intellium_db

# Run migrations
kubectl exec -it deployment/backend -n intellium -- alembic upgrade head

# Delete everything
kubectl delete namespace intellium
```

## ✅ Pre-Deployment Checklist

- [ ] Build Docker image: `docker build -t intellium/backend:latest .`
- [ ] Push to registry: `docker push intellium/backend:latest`
- [ ] Update `secrets.yaml` with base64-encoded values
- [ ] Update `ingress.yaml` with your domain
- [ ] Update `configmap.yaml` CORS_ORIGINS
- [ ] Install nginx-ingress-controller
- [ ] Install cert-manager
- [ ] Configure DNS A records to Ingress IP
- [ ] Review resource limits
- [ ] Test backup/restore procedures

## 🔍 Troubleshooting

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n intellium
kubectl logs <pod-name> -n intellium
```

**Database connection issues:**
```bash
kubectl exec -it deployment/backend -n intellium -- nc -zv postgres-service 5432
kubectl logs statefulset/postgres -n intellium
```

**Certificate not issuing:**
```bash
kubectl get certificate -n intellium
kubectl describe certificate intellium-tls -n intellium
kubectl logs -n cert-manager deployment/cert-manager
```

**Ingress not working:**
```bash
kubectl get ingress -n intellium
kubectl describe ingress intellium-ingress -n intellium
kubectl get ingress intellium-ingress -n intellium -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

## 📚 Documentation

See `README.md` for:
- Complete architecture diagram
- Detailed configuration guide
- Security best practices
- Production checklist
- Advanced operations
- Disaster recovery

## 🎯 Architecture

```
Internet → Ingress (TLS) → Backend Service → Backend Pods (3-10)
                                           ↓
                                    PostgreSQL (StatefulSet)
                                    Redis (Deployment)
                                           ↑
                              Celery Workers (2-8 pods)
```

## 🚦 Health Checks

All services include:
- **Liveness probes** - Restart if unhealthy
- **Readiness probes** - Remove from load balancer if not ready
- **Startup probes** - Allow time for initialization

## 📊 Monitoring

Prometheus annotations on backend pods:
```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "8000"
prometheus.io/path: "/metrics"
```

Deploy Prometheus to scrape metrics automatically.

---

**Ready to deploy! 🚀**

```bash
cd infra/kubernetes
./deploy.sh
```
