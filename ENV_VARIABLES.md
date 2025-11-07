# Environment Variables - Quick Reference

## 🔐 Production Environment Variables

### Backend (Render.com)

#### Required
```bash
# Database (auto-populated by Render)
DATABASE_URL=${DATABASE_URL}

# Redis (from Upstash)
REDIS_URL=rediss://default:YOUR_PASSWORD@YOUR_HOST:6379

# Security
SECRET_KEY=<generate-64-char-random-string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (replace with your Vercel URL)
CORS_ORIGINS=https://intellium-admin.vercel.app,https://intellium.vercel.app

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
JSON_LOGS=true

# Performance
DB_POOL_SIZE=20
DB_POOL_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100

# Monitoring
ENABLE_METRICS=true
```

#### Optional (for full features)
```bash
# Stripe Payment
STRIPE_API_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@intellium.app

# AWS S3 Storage
STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=intellium-uploads
AWS_REGION=eu-central-1

# Sentry Error Tracking
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

---

### Web Admin (Vercel)

```bash
# API URL (replace with your Render URL)
NEXT_PUBLIC_API_URL=https://intellium-backend.onrender.com
```

---

### Mobile Apps

#### Android (build.gradle.kts)
```kotlin
// In ApiConfig.kt, change:
private const val API_ENVIRONMENT = "production"

// Production URL (already set):
private const val PRODUCTION_API_URL = "https://intellium-backend.onrender.com"
```

#### iOS (AppConfig.swift)
```swift
// In AppConfig.swift, change:
static let current: Environment = .production

// Production URL (already set):
private static let productionURL = "https://intellium-backend.onrender.com"
```

---

## 🛠️ Development Environment Variables

### Backend (Local)

Create `.env` file in `backend/`:
```bash
# Database (local PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/intellium

# Redis (local)
REDIS_URL=redis://localhost:6379/0

# MinIO (local S3)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_URL=http://localhost:9000
MINIO_BUCKET_NAME=intellium

# Security (development)
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (local development)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
JSON_LOGS=false

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Admin
FIRST_SUPERUSER_EMAIL=admin@patentguard.com
FIRST_SUPERUSER_PASSWORD=changethis

# Performance (lower for local)
DB_POOL_SIZE=5
DB_POOL_MAX_OVERFLOW=10
RATE_LIMIT_ENABLED=false
```

---

### Web Admin (Local)

Create `.env.local` file in `web-admin/`:
```bash
# API URL (local backend)
NEXT_PUBLIC_API_URL=http://localhost:8000

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

### Mobile Apps (Local)

#### Android (ApiConfig.kt)
```kotlin
private const val API_ENVIRONMENT = "development"
private const val DEBUG_API_URL = "http://10.0.2.2:8000"  // Android emulator
```

#### iOS (AppConfig.swift)
```swift
static let current: Environment = .development
private static let developmentURL = "http://localhost:8000"  // iOS simulator
```

---

## 🔑 How to Generate Secrets

### SECRET_KEY (64 characters)
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(48))"

# OpenSSL
openssl rand -base64 48
```

### Stripe Keys
1. Go to [dashboard.stripe.com](https://dashboard.stripe.com)
2. Get API keys from Developers → API keys
3. Use **live keys** for production, **test keys** for development

### AWS S3 Credentials
1. Go to AWS IAM Console
2. Create a new user with `AmazonS3FullAccess` policy
3. Generate access key and secret key
4. Create S3 bucket in your preferred region

### Sentry DSN
1. Go to [sentry.io](https://sentry.io)
2. Create a new project
3. Copy the DSN from Settings → Client Keys

---

## 📝 Notes

### Production Checklist
- [ ] `DATABASE_URL` - Auto-populated by Render
- [ ] `REDIS_URL` - From Upstash dashboard
- [ ] `SECRET_KEY` - Generate random string (48+ chars)
- [ ] `CORS_ORIGINS` - Update with your Vercel URL
- [ ] `STRIPE_API_KEY` - From Stripe dashboard (optional)
- [ ] `STRIPE_WEBHOOK_SECRET` - From Stripe webhooks (optional)
- [ ] `AWS_*` - From AWS IAM (if using S3)
- [ ] `SENTRY_DSN` - From Sentry (optional)

### Security Best Practices
- ✅ Never commit `.env` files to git
- ✅ Use different secrets for dev/staging/production
- ✅ Rotate secrets regularly (every 90 days)
- ✅ Use environment variables in CI/CD (GitHub Secrets)
- ✅ Keep `SECRET_KEY` at least 64 characters
- ✅ Enable 2FA on Stripe, AWS, and Sentry accounts

### Free Tier Limits
- **Render PostgreSQL**: 256 MB RAM, 1 GB storage, expires in 90 days
- **Upstash Redis**: 10,000 commands/day, 256 MB storage
- **Vercel**: 100 GB bandwidth/month
- **Render Web Service**: 750 hours/month, auto-sleeps after 15 min

### Environment File Locations
```
Intellium/
├── backend/
│   ├── .env                    # Local development
│   ├── .env.example            # Template
│   └── .env.production         # Production template (don't commit)
├── web-admin/
│   ├── .env.local              # Local development
│   └── .env.production         # Production (set in Vercel)
└── mobile/
    ├── shared/.../ApiConfig.kt      # Android/KMM config
    └── iosApp/.../AppConfig.swift   # iOS config
```

---

## 🔄 Updating Environment Variables

### Render (Backend)
1. Go to Render dashboard
2. Select your web service
3. Go to "Environment" tab
4. Add/edit variables
5. Click "Save Changes"
6. Service will auto-redeploy

### Vercel (Web Admin)
1. Go to Vercel dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add/edit variables
5. Click "Save"
6. Redeploy from Deployments tab

### Mobile Apps
1. Update `ApiConfig.kt` (Android) or `AppConfig.swift` (iOS)
2. Rebuild the app
3. Reinstall on devices

---

## 📞 Support

If you need help with environment variables:
- Check [DEPLOYMENT_URLS.md](DEPLOYMENT_URLS.md) for detailed setup
- Check [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) for overview
- Open an issue on GitHub

---

**Remember**: Keep your production secrets secure! 🔐
