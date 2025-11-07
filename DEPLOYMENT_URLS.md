# Deployment Guide - Production URLs

## 🌐 Live URLs

### Backend API
- **Production URL**: `https://intellium-backend.onrender.com`
- **API Documentation**: `https://intellium-backend.onrender.com/docs`
- **Health Check**: `https://intellium-backend.onrender.com/health`
- **Status**: Free tier (auto-sleeps after 15 min inactivity, 750 hours/month)

### Web Admin Dashboard
- **Production URL**: `https://intellium-admin.vercel.app`
- **Status**: Free tier (unlimited deployments)

---

## 🚀 Deployment Instructions

### Backend Deployment (Render.com)

#### 1. Sign Up & Create Account
1. Go to [render.com](https://render.com) and sign up
2. Connect your GitHub account

#### 2. Create Web Service
1. Click "New +" → "Web Service"
2. Connect to your GitHub repository: `yourusername/Intellium`
3. Configure:
   - **Name**: `intellium-backend`
   - **Region**: Frankfurt (or closest to users)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
   - **Plan**: Free

#### 3. Create PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `intellium-db`
   - **Database**: `intellium`
   - **Region**: Same as web service
   - **Plan**: Free (expires in 90 days, migrate data before expiry)

#### 4. Setup Redis (Upstash)
Since Render doesn't offer free Redis, use Upstash:
1. Go to [upstash.com](https://upstash.com) and sign up
2. Create a Redis database
3. Copy the connection string (format: `rediss://default:password@host:port`)

#### 5. Configure Environment Variables
In Render dashboard for your web service, add these environment variables:

**Required:**
```bash
# Database (auto-populated by Render)
DATABASE_URL=${DATABASE_URL}

# Redis (from Upstash)
REDIS_URL=rediss://default:YOUR_PASSWORD@YOUR_HOST:6379

# Security
SECRET_KEY=<generate-random-64-char-string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (update with your Vercel URL)
CORS_ORIGINS=https://intellium-admin.vercel.app,https://intellium.vercel.app

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
JSON_LOGS=true

# Performance
DB_POOL_SIZE=20
DB_POOL_MAX_OVERFLOW=10
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
ENABLE_METRICS=true
```

**Optional (for full features):**
```bash
# Stripe Payment
STRIPE_API_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Email (if using email features)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@intellium.app

# File Storage (AWS S3)
STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=intellium-uploads
AWS_REGION=eu-central-1
```

#### 6. Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy
3. Wait 5-10 minutes for first deployment
4. Check logs for any errors
5. Visit `https://intellium-backend.onrender.com/health` to verify

---

### Web Admin Deployment (Vercel)

#### 1. Sign Up & Create Account
1. Go to [vercel.com](https://vercel.com) and sign up
2. Connect your GitHub account

#### 2. Import Project
1. Click "Add New" → "Project"
2. Import your GitHub repository: `yourusername/Intellium`
3. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `web-admin`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

#### 3. Configure Environment Variables
Add this environment variable in Vercel dashboard:

```bash
NEXT_PUBLIC_API_URL=https://intellium-backend.onrender.com
```

#### 4. Deploy
1. Click "Deploy"
2. Vercel will automatically build and deploy
3. Visit your Vercel URL (e.g., `https://intellium-admin.vercel.app`)

#### 5. Setup Custom Domain (Optional)
1. Go to Project Settings → Domains
2. Add your custom domain (e.g., `admin.intellium.app`)
3. Follow DNS configuration instructions

---

## 📱 Mobile App Configuration

### For Production Testing

#### Android
1. Open `mobile/shared/src/commonMain/kotlin/com/patentguard/shared/network/ApiConfig.kt`
2. Change:
   ```kotlin
   private const val API_ENVIRONMENT = "production"
   ```
3. Build release APK:
   ```bash
   cd mobile/androidApp
   ./gradlew assembleRelease
   ```
4. APK location: `mobile/androidApp/build/outputs/apk/release/androidApp-release.apk`
5. Install on device: `adb install androidApp-release.apk`

#### iOS
1. Open `mobile/iosApp/iosApp/Config/AppConfig.swift`
2. Change:
   ```swift
   static let current: Environment = .production
   ```
3. Build in Xcode:
   - Select "Any iOS Device (arm64)"
   - Product → Archive
   - Distribute to TestFlight or Ad-Hoc for testing
4. Install on device via TestFlight or iTunes

### For Development (Localhost)
Keep the environment setting as `.development` (iOS) or `"development"` (Android) to use localhost.

---

## 🧪 Testing on Real Devices

### Backend Health Check
```bash
curl https://intellium-backend.onrender.com/health
# Expected: {"status":"ok","database":"healthy","environment":"production"}
```

### Test Authentication
```bash
curl -X POST https://intellium-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@patentguard.com","password":"changethis"}'
```

### Mobile App Testing
1. **Android**:
   - Install production APK on device
   - Open app and try to login
   - Check logs: `adb logcat | grep PatentGuard`
   
2. **iOS**:
   - Install via TestFlight or Ad-Hoc
   - Open app and try to login
   - Check Xcode console for logs

3. **Expected Behavior**:
   - App connects to `https://intellium-backend.onrender.com`
   - Login succeeds with correct credentials
   - API calls work over HTTPS
   - No SSL/TLS errors

---

## ⚡ Performance Optimization

### Current Configuration (50-100 Users)

**Database Connection Pooling:**
- Pool Size: 20 connections
- Max Overflow: 10 connections
- Total: Up to 30 concurrent connections

**Rate Limiting:**
- 100 requests per minute per IP
- Prevents abuse and ensures fair usage

**Caching:**
- Redis cache for frequently accessed data
- Reduces database load

**Monitoring:**
- Prometheus metrics enabled at `/metrics`
- Health checks every 30 seconds
- Sentry error tracking (if configured)

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test with 50 concurrent users, 1000 requests
ab -n 1000 -c 50 https://intellium-backend.onrender.com/health

# Expected: >95% success rate, <500ms average response time
```

### Scaling Beyond 100 Users
If you exceed 100 concurrent users:
1. Upgrade Render plan to paid tier (more CPU/RAM)
2. Increase `DB_POOL_SIZE` to 50
3. Add multiple Render instances with load balancer
4. Migrate to paid PostgreSQL plan
5. Consider CDN for static assets (Cloudflare)

---

## 🔒 Security Checklist

- [x] HTTPS enabled on both backend and frontend
- [x] CORS configured with specific origins (no wildcard *)
- [x] Rate limiting enabled
- [x] Environment variables for secrets (not in code)
- [x] SQL injection protection (SQLAlchemy ORM)
- [x] Authentication tokens expire after 30 minutes
- [ ] Setup Sentry for error tracking
- [ ] Enable WAF (Web Application Firewall) on Cloudflare
- [ ] Regular security updates for dependencies

---

## 📊 Monitoring & Logs

### Backend Logs (Render)
1. Go to Render dashboard → intellium-backend
2. Click "Logs" tab
3. Real-time logs with structured JSON format

### Web Admin Logs (Vercel)
1. Go to Vercel dashboard → intellium-admin
2. Click "Deployments" → Select deployment → "Logs"
3. Build and runtime logs available

### Database Monitoring (Render)
1. Go to Render dashboard → intellium-db
2. View connection count, storage usage
3. **Important**: Free tier expires in 90 days, set reminder!

### Uptime Monitoring
Use free tools:
- [UptimeRobot](https://uptimerobot.com) - Monitor `/health` endpoint
- [Better Uptime](https://betteruptime.com) - 10 monitors free
- Set up alerts for downtime

---

## 🐛 Troubleshooting

### Backend won't start
- Check Render logs for error messages
- Verify all required environment variables are set
- Check database connection string is correct
- Ensure PostgreSQL database exists and is running

### Mobile app can't connect
- Verify API_ENVIRONMENT is set to "production" (Android) or `.production` (iOS)
- Check device has internet connection
- Test backend URL in browser: `https://intellium-backend.onrender.com/health`
- Check for SSL errors in mobile logs

### CORS errors in web admin
- Verify `CORS_ORIGINS` includes your Vercel URL
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Clear browser cache
- Check browser console for exact error message

### Database connection errors
- Free tier PostgreSQL expires after 90 days
- Check Render dashboard for database status
- Verify `DATABASE_URL` environment variable
- Check connection pool settings aren't too high

### Slow performance
- **Cold starts**: Free tier sleeps after 15 min inactivity, first request takes 30-60 seconds
- **Solution**: Upgrade to paid tier ($7/month) for always-on service
- Or: Setup cron job to ping every 10 minutes: [Cron-Job.org](https://cron-job.org)

---

## 📅 Maintenance Tasks

### Weekly
- Check Render logs for errors
- Monitor database storage usage
- Review rate limit violations

### Monthly
- Review Uptime Robot reports
- Check Vercel bandwidth usage
- Update dependencies (`npm audit`, `pip list --outdated`)

### Before 90-day Expiry (Free DB)
- Export database data
- Create new PostgreSQL instance
- Import data to new database
- Update `DATABASE_URL` environment variable

---

## 🎯 Next Steps

1. **Deploy Backend to Render** ✅
2. **Deploy Web Admin to Vercel** ✅
3. **Configure Mobile Apps for Production** ✅
4. **Test on Real Devices** ⏳
5. **Setup Monitoring** ⏳
6. **Add Custom Domains** (Optional)
7. **Enable Sentry Error Tracking** (Optional)
8. **Setup Automated Backups** (Recommended)

---

## 📞 Support

For deployment issues:
- **Render**: [render.com/docs](https://render.com/docs)
- **Vercel**: [vercel.com/docs](https://vercel.com/docs)
- **Upstash**: [upstash.com/docs](https://upstash.com/docs)

Project issues: Open an issue on GitHub repository
