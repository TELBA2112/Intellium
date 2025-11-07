# Middleware & Monitoring Setup Guide

## Overview

This guide covers the middleware and monitoring infrastructure added to the Intellium Patent Guard backend:

1. **Request Logging Middleware** - Structured logging with loguru
2. **Rate Limiting** - Protection against abuse with SlowAPI
3. **Error Handling** - Centralized error responses
4. **JWT Verification** - Protected endpoint authentication
5. **Prometheus Metrics** - Application monitoring
6. **Grafana Dashboards** - Visualization

## Middleware Components

### 1. Request Logging Middleware

**File:** `app/middleware/logging_middleware.py`

Logs all HTTP requests and responses with:
- Request method, path, client IP
- Query parameters
- Response status code
- Processing time in milliseconds
- Error details (if any)

**Features:**
- Structured JSON logging
- Request/response timing
- Custom headers (X-Process-Time)
- Exception tracking

**Usage:**
```python
# Automatically applied to all routes
# Logs are output to console and files (configured in app/core/logging.py)
```

### 2. Rate Limiting

**File:** `app/middleware/rate_limit.py`

Prevents API abuse with configurable limits:
- Global limits: 100 requests/minute, 1000 requests/hour
- Per-endpoint custom limits
- User-based or IP-based identification

**Features:**
- Fixed-window rate limiting
- Custom limits per endpoint
- User-aware rate limiting (authenticated users tracked by ID)
- Automatic 429 Too Many Requests responses

**Usage:**
```python
from app.middleware import limiter

@router.post("/login")
@limiter.limit("10/minute")  # Custom limit
async def login(request: Request, ...):
    ...
```

**Current Rate Limits:**
- Registration: 5/minute
- Login: 10/minute
- Default: 100/minute, 1000/hour

### 3. Error Handling

**File:** `app/middleware/error_handler.py`

Centralized error handling with standardized responses:

**Error Types Handled:**
- HTTP exceptions (4xx, 5xx)
- Validation errors (422)
- Database errors (500)
- Unexpected exceptions (500)

**Response Format:**
```json
{
  "error": "ERROR_TYPE",
  "message": "Human-readable message",
  "details": {...},
  "path": "/api/endpoint"
}
```

**Features:**
- Structured error logging
- Consistent error responses
- Security (hides internal details)
- Path tracking

### 4. JWT Verification

**Updated:** `app/api/auth.py`

All protected endpoints now use the `get_current_user` dependency:

**Features:**
- JWT token decoding
- User lookup from database
- Request state management (for rate limiting)
- Automatic 401 responses for invalid tokens

**Usage:**
```python
@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    # current_user is verified and loaded from DB
    return {"user": current_user.email}
```

## Monitoring Setup

### 1. Prometheus Metrics

**File:** `app/monitoring/metrics.py`

**Metrics Exposed:**
- `http_requests_total` - Total HTTP requests (by method, endpoint, status)
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_inprogress` - Current requests being processed
- `app_info` - Application metadata

**Endpoint:** `http://localhost:8000/metrics`

**Custom Metrics:**
```python
from app.monitoring import track_request

track_request("POST", "/api/auth/login", 200)
```

### 2. Docker Compose Services

**File:** `docker-compose.yml`

**Services Added:**
- **Prometheus** - Metrics collection (port 9090)
- **Grafana** - Visualization dashboard (port 3000)

**Configuration:**
- Prometheus scrapes backend metrics every 10 seconds
- Grafana auto-provisioned with datasource and dashboards
- Persistent volumes for data retention

### 3. Prometheus Configuration

**File:** `infra/prometheus/prometheus.yml`

**Scrape Configs:**
- Backend API: `backend:8000/metrics` (10s interval)
- Prometheus self-monitoring
- Placeholders for PostgreSQL and Redis exporters

### 4. Grafana Setup

**Datasource:** `infra/grafana/provisioning/datasources/prometheus.yml`
- Auto-configured Prometheus connection
- 15-second refresh interval

**Dashboard:** `infra/grafana/dashboards/fastapi-metrics.json`

**Panels:**
1. **Request Rate** - Requests per second (by method/handler)
2. **Response Time** - p95 and p99 percentiles
3. **HTTP Status Codes** - Distribution of status codes
4. **Requests In Progress** - Current active requests

**Access:**
- URL: `http://localhost:3000`
- Username: `admin`
- Password: `admin`

## Running the Stack

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check service health
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Services URLs

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Metrics:** http://localhost:8000/metrics
- **Health Check:** http://localhost:8000/health
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000

### Manual Setup (Development)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run application
python -m app.main

# Or with uvicorn
uvicorn app.main:app --reload
```

## Environment Variables

Required environment variables (set in `.env` or docker-compose):

```bash
# Security
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Rate Limiting
ENABLE_METRICS=true
```

## Testing Middleware

### Test Request Logging

```bash
curl http://localhost:8000/health
# Check logs for structured output
```

### Test Rate Limiting

```bash
# Exceed rate limit (run multiple times)
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/auth/login
done
# Should receive 429 Too Many Requests
```

### Test Error Handling

```bash
# Invalid request
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid"}'
# Should receive structured 422 error
```

### Test JWT Verification

```bash
# Without token
curl http://localhost:8000/api/auth/me
# Should receive 401 Unauthorized

# With valid token
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
# Should return user data
```

### Test Metrics

```bash
# Generate some traffic
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Check metrics
curl http://localhost:8000/metrics
# Should see Prometheus-format metrics
```

## Monitoring Best Practices

### 1. Prometheus Queries

```promql
# Request rate by endpoint
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Requests in progress
http_requests_inprogress
```

### 2. Alerting

Add alerts in `prometheus.yml`:

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
```

### 3. Log Analysis

Logs are structured JSON (when `JSON_LOGS=true`):

```json
{
  "timestamp": "2025-11-07T12:00:00.000Z",
  "level": "INFO",
  "message": "Request completed",
  "method": "GET",
  "path": "/api/auth/me",
  "status_code": 200,
  "process_time_ms": 45.2,
  "client_ip": "172.18.0.1"
}
```

## Security Considerations

1. **Rate Limiting:**
   - Adjust limits based on load testing
   - Consider Redis backend for distributed rate limiting

2. **JWT Tokens:**
   - Tokens expire after 30 minutes
   - Use refresh tokens for longer sessions
   - Store SECRET_KEY securely

3. **Error Messages:**
   - Generic messages to external users
   - Detailed logs for internal monitoring
   - Never expose stack traces in production

4. **CORS:**
   - Configure `CORS_ORIGINS` for allowed domains
   - Avoid wildcard (*) in production

## Performance Tuning

### Rate Limiting Storage

For production, use Redis instead of in-memory:

```python
# In app/middleware/rate_limit.py
limiter = Limiter(
    key_func=get_client_identifier,
    storage_uri="redis://redis:6379/1",  # Use Redis
)
```

### Metrics Cardinality

Keep metric labels low-cardinality:
- ✅ Good: `{method="GET", status="200"}`
- ❌ Bad: `{user_id="12345", ip="1.2.3.4"}`

### Log Levels

Adjust log levels by environment:
- **Development:** DEBUG
- **Production:** INFO or WARNING
- **Critical Issues:** ERROR

## Troubleshooting

### Metrics Not Showing

1. Check backend is running: `curl http://localhost:8000/health`
2. Check metrics endpoint: `curl http://localhost:8000/metrics`
3. Check Prometheus targets: http://localhost:9090/targets
4. Verify Grafana datasource: http://localhost:3000/datasources

### Rate Limiting Not Working

1. Verify `slowapi` is installed
2. Check middleware is registered in `app/main.py`
3. Test with curl/scripts exceeding limits
4. Check logs for rate limit messages

### Logs Not Appearing

1. Verify `loguru` is installed
2. Check `logs/` directory exists
3. Verify `LOG_LEVEL` environment variable
4. Check console output (stdout)

### Grafana Dashboard Empty

1. Wait a few minutes for data collection
2. Generate traffic: `for i in {1..100}; do curl http://localhost:8000/health; done`
3. Adjust time range (top-right corner)
4. Check Prometheus is scraping: http://localhost:9090/targets

## Summary

✅ **Request Logging** - All requests logged with structured data  
✅ **Rate Limiting** - 5/min registration, 10/min login, 100/min default  
✅ **Error Handling** - Centralized with standardized responses  
✅ **JWT Verification** - All protected endpoints verified  
✅ **Prometheus Metrics** - Exposed at `/metrics`  
✅ **Grafana Dashboard** - Pre-configured FastAPI metrics  
✅ **Docker Compose** - Complete monitoring stack  

The backend now has production-ready middleware and monitoring!
