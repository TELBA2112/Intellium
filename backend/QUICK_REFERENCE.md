# Middleware & Monitoring Quick Reference

## 🚀 Quick Start

```bash
# Setup
cd backend
./setup.sh

# Start all services
cd ..
docker-compose up -d

# View logs
docker-compose logs -f backend

# Access services
open http://localhost:8000/docs      # API Docs
open http://localhost:9090           # Prometheus
open http://localhost:3000           # Grafana (admin/admin)
```

## 🔒 Middleware Features

### Request Logging
```python
# Automatically logs all requests
# Output includes: method, path, status, timing, client IP
```

### Rate Limiting
```python
from app.middleware import limiter

@router.post("/endpoint")
@limiter.limit("5/minute")  # Custom limit
async def endpoint(request: Request, ...):
    pass
```

**Default Limits:**
- Registration: `5/minute`
- Login: `10/minute`
- Global: `100/minute`, `1000/hour`

### Error Handling
```python
# Automatic standardized error responses
{
  "error": "ERROR_TYPE",
  "message": "Human readable",
  "details": {...},
  "path": "/api/endpoint"
}
```

### JWT Authentication
```python
from app.api.auth import get_current_user

@router.get("/protected")
async def protected(user: User = Depends(get_current_user)):
    return {"user_id": user.id}
```

## 📊 Monitoring

### Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

### Key Metrics
- `http_requests_total` - Request count by method/endpoint/status
- `http_request_duration_seconds` - Response time histogram
- `http_requests_inprogress` - Active requests
- `app_info` - Application metadata

### Prometheus Queries
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Response time p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Grafana Dashboard
- URL: http://localhost:3000
- User: `admin` / Pass: `admin`
- Dashboard: "Intellium FastAPI Metrics"

## 🛠️ Testing

### Test Rate Limiting
```bash
# Exceed limit
for i in {1..15}; do curl -X POST http://localhost:8000/api/auth/login; done
# Should get 429 Too Many Requests
```

### Test JWT
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -d "username=user@example.com&password=pass" | jq -r .access_token)

# Use token
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Test Metrics
```bash
# Generate traffic
for i in {1..100}; do curl http://localhost:8000/health; done

# Check metrics
curl http://localhost:8000/metrics | grep http_requests_total
```

## 📝 Environment Variables

```bash
# Required
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0

# Optional
ENVIRONMENT=development
DEBUG=true
ENABLE_METRICS=true
LOG_LEVEL=INFO
JSON_LOGS=false
```

## 🔧 Common Tasks

### View Logs
```bash
# Docker
docker-compose logs -f backend

# Local
tail -f logs/app.log
```

### Check Health
```bash
curl http://localhost:8000/health
```

### Run Tests
```bash
pytest -v
pytest --cov=app --cov-report=html
```

### Format Code
```bash
black app/ tests/
isort app/ tests/
```

### Lint
```bash
flake8 app/ tests/
mypy app/
```

## 🐛 Troubleshooting

### Metrics Not Showing
1. Check `/metrics`: `curl http://localhost:8000/metrics`
2. Check Prometheus targets: http://localhost:9090/targets
3. Generate traffic to populate metrics

### Rate Limit Not Working
1. Check middleware registered in `app/main.py`
2. Verify `slowapi` installed: `pip list | grep slowapi`
3. Test with curl loop

### JWT Invalid
1. Check token format: `Bearer <token>`
2. Verify SECRET_KEY in .env
3. Check token expiration (30 min default)

### Grafana Empty
1. Wait 1-2 minutes for data collection
2. Adjust time range (top right)
3. Generate traffic with curl loop

## 📦 Dependencies

```txt
# Middleware
slowapi==0.1.9

# Monitoring
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0

# Logging (already added)
loguru==0.7.2
```

## 🎯 Best Practices

1. **Rate Limiting**: Adjust limits based on load testing
2. **Logging**: Use INFO in production, DEBUG in development
3. **Metrics**: Keep label cardinality low
4. **JWT**: Rotate SECRET_KEY regularly
5. **CORS**: Specify exact origins in production
6. **Errors**: Never expose stack traces to clients

## 🔗 Links

- [SlowAPI Docs](https://slowapi.readthedocs.io/)
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Loguru Docs](https://loguru.readthedocs.io/)
