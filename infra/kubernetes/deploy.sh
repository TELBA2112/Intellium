#!/bin/bash

# Kubernetes Deployment Script for Intellium Patent Guard
# This script deploys all Kubernetes resources

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Intellium Kubernetes Deployment${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Check cluster connection
echo "Checking cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected to cluster${NC}"
echo ""

# Get current context
CONTEXT=$(kubectl config current-context)
echo -e "${YELLOW}Current context: $CONTEXT${NC}"
read -p "Do you want to deploy to this cluster? (yes/no) " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi
echo ""

# Create namespace
echo "Creating namespace..."
kubectl apply -f namespace.yaml
echo -e "${GREEN}✓ Namespace created${NC}"
echo ""

# Update secrets
echo -e "${YELLOW}⚠ IMPORTANT: Update secrets.yaml with your actual base64-encoded credentials${NC}"
read -p "Have you updated secrets.yaml? (yes/no) " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo -e "${YELLOW}Please update secrets.yaml and run this script again${NC}"
    exit 0
fi

# Apply ConfigMap and Secrets
echo "Applying ConfigMap and Secrets..."
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
echo -e "${GREEN}✓ ConfigMap and Secrets applied${NC}"
echo ""

# Deploy PostgreSQL
echo "Deploying PostgreSQL..."
kubectl apply -f postgres.yaml
echo -e "${GREEN}✓ PostgreSQL deployed${NC}"
echo ""

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n intellium --timeout=300s
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
echo ""

# Deploy Redis
echo "Deploying Redis..."
kubectl apply -f redis.yaml
echo -e "${GREEN}✓ Redis deployed${NC}"
echo ""

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n intellium --timeout=300s
echo -e "${GREEN}✓ Redis is ready${NC}"
echo ""

# Deploy Backend
echo "Deploying Backend..."
kubectl apply -f backend.yaml
echo -e "${GREEN}✓ Backend deployed${NC}"
echo ""

# Wait for Backend to be ready
echo "Waiting for Backend to be ready..."
kubectl wait --for=condition=ready pod -l app=backend -n intellium --timeout=300s
echo -e "${GREEN}✓ Backend is ready${NC}"
echo ""

# Deploy Celery Workers
echo "Deploying Celery Workers..."
kubectl apply -f celery-worker.yaml
echo -e "${GREEN}✓ Celery Workers deployed${NC}"
echo ""

# Deploy HPA
echo "Deploying Horizontal Pod Autoscalers..."
kubectl apply -f hpa.yaml
echo -e "${GREEN}✓ HPA deployed${NC}"
echo ""

# Deploy Network Policies
echo "Deploying Network Policies..."
kubectl apply -f network-policy.yaml
echo -e "${GREEN}✓ Network Policies deployed${NC}"
echo ""

# Deploy Ingress
echo "Deploying Ingress..."
echo -e "${YELLOW}Note: Make sure nginx-ingress-controller and cert-manager are installed${NC}"
read -p "Deploy Ingress now? (yes/no) " -r
if [[ $REPLY =~ ^[Yy]es$ ]]; then
    kubectl apply -f ingress.yaml
    echo -e "${GREEN}✓ Ingress deployed${NC}"
else
    echo -e "${YELLOW}Skipping Ingress deployment${NC}"
fi
echo ""

# Display status
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Deployment Complete!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "Checking deployment status..."
echo ""

echo "Pods:"
kubectl get pods -n intellium
echo ""

echo "Services:"
kubectl get services -n intellium
echo ""

echo "Ingress:"
kubectl get ingress -n intellium
echo ""

echo -e "${GREEN}Deployment successful! 🚀${NC}"
echo ""
echo "Useful commands:"
echo "  - View logs:           kubectl logs -f deployment/backend -n intellium"
echo "  - Check pods:          kubectl get pods -n intellium"
echo "  - Describe pod:        kubectl describe pod <pod-name> -n intellium"
echo "  - Port forward:        kubectl port-forward svc/backend-service 8000:8000 -n intellium"
echo "  - Scale deployment:    kubectl scale deployment/backend --replicas=5 -n intellium"
echo "  - Delete all:          kubectl delete namespace intellium"
echo ""
echo -e "${YELLOW}Don't forget to:${NC}"
echo "  1. Update DNS records to point to your Ingress IP"
echo "  2. Wait for TLS certificates to be issued (check: kubectl get certificate -n intellium)"
echo "  3. Monitor the deployment (kubectl get pods -n intellium -w)"
