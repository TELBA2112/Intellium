# Intellium - Patent Guard Platform

> Smart patent similarity checking and document management system

## 🌐 Production URLs

### Live Deployments
- **Backend API**: https://intellium-backend.onrender.com
  - API Documentation: https://intellium-backend.onrender.com/docs
  - Health Check: https://intellium-backend.onrender.com/health
  
- **Web Admin Dashboard**: https://intellium-admin.vercel.app

### Mobile Apps
- **Android**: Build and install production APK (see deployment guide)
- **iOS**: Build and install via TestFlight (see deployment guide)

---

## 🚀 Quick Start

### For Developers

**Clone the repository:**
```bash
git clone https://github.com/yourusername/Intellium.git
cd Intellium
```

**Backend (Local Development):**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit .env with your settings
uvicorn app.main:app --reload
```

**Web Admin (Local Development):**
```bash
cd web-admin
npm install
cp .env.local.example .env.local  # Edit .env.local
npm run dev
```

**Mobile (Local Development):**
```bash
cd mobile

# Android
cd androidApp
./gradlew installDebug

# iOS
cd ../iosApp
open iosApp.xcodeproj
# Build and run in Xcode
```

---

## 📦 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Storage**: MinIO (local), AWS S3 (production)
- **Task Queue**: Celery
- **Payments**: Stripe
- **Monitoring**: Prometheus + Grafana

### Web Admin
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **i18n**: next-i18next (Uzbek, Russian, English)

### Mobile (Kotlin Multiplatform)
- **Shared**: Kotlin Multiplatform (KMM)
- **Network**: Ktor Client
- **Serialization**: kotlinx.serialization
- **Android**: Jetpack Compose
- **iOS**: SwiftUI
- **Languages**: Uzbek, Russian, English

---

## 🌍 Internationalization (i18n)

The platform supports three languages:
- 🇺🇿 Uzbek (uz)
- 🇷🇺 Russian (ru)
- 🇬🇧 English (en)

Language switching is available in all apps (web, Android, iOS).

---

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Mobile Apps                          │
│  ┌──────────────┐              ┌──────────────┐        │
│  │   Android    │              │     iOS      │        │
│  │  (Compose)   │              │  (SwiftUI)   │        │
│  └──────┬───────┘              └──────┬───────┘        │
│         │                             │                 │
│         └─────────────┬───────────────┘                │
│                       │                                  │
│              ┌────────▼────────┐                       │
│              │  KMM Shared     │                       │
│              │  SDK            │                       │
│              └────────┬────────┘                       │
└───────────────────────┼──────────────────────────────┘
                        │
                        │ HTTPS/REST API
                        │
        ┌───────────────▼───────────────┐
        │      Web Admin (Next.js)      │
        └───────────────┬───────────────┘
                        │
                        │ HTTPS/REST API
                        │
        ┌───────────────▼───────────────┐
        │    FastAPI Backend            │
        │  ┌─────────────────────────┐  │
        │  │  Auth │ Documents │ AI  │  │
        │  └─────────────────────────┘  │
        └───────────────┬───────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
    ┌───▼────┐  ┌──────┐  ┌──────┐  ┌─▼──┐
    │  DB    │  │Redis │  │MinIO │  │Cel-│
    │(Postgres) │(Cache) │(Files) │ │ery │
    └────────┘  └──────┘  └──────┘  └────┘
```

---

## 📱 Features

### Core Features
- ✅ User authentication & authorization
- ✅ Patent document upload
- ✅ AI-powered similarity checking
- ✅ Document management
- ✅ Payment processing (Stripe)
- ✅ Multi-language support (UZ/RU/EN)

### Admin Features
- ✅ User management
- ✅ Document moderation
- ✅ Analytics dashboard
- ✅ System monitoring

### Mobile Features
- ✅ Native Android & iOS apps
- ✅ Document camera integration
- ✅ Offline support
- ✅ Push notifications

---

## 🚀 Deployment

### Production (Free Tier)
- **Backend**: Render.com (Free tier, auto-sleeps after 15 min)
- **Web Admin**: Vercel (Free tier, unlimited deployments)
- **Database**: Render PostgreSQL (Free, expires in 90 days)
- **Cache**: Upstash Redis (Free, 10k commands/day)
- **Performance**: Optimized for 50-100 concurrent users

### Deployment Guides
- 📖 **Complete Guide**: [DEPLOYMENT_URLS.md](DEPLOYMENT_URLS.md)
- 📝 **Summary**: [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
- ⚙️ **Config**: [render.yaml](render.yaml)

### Quick Deploy

**1. Backend to Render:**
```bash
# Push to GitHub, Render auto-deploys from main branch
git push origin main
```

**2. Web to Vercel:**
```bash
# Push to GitHub, Vercel auto-deploys from main branch
git push origin main
```

**3. Mobile Apps:**
```bash
# Android
cd mobile/androidApp
./gradlew assembleRelease

# iOS
cd mobile/iosApp
# Archive in Xcode → Distribute to TestFlight
```

See [DEPLOYMENT_URLS.md](DEPLOYMENT_URLS.md) for detailed instructions.

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Web Admin Tests
```bash
cd web-admin
npm test
```

### Mobile Tests
```bash
cd mobile
./gradlew testDebugUnitTest  # Android
```

### Load Testing
```bash
# Test with 50 concurrent users
ab -n 1000 -c 50 https://intellium-backend.onrender.com/health
```

---

## 📊 Performance

### Current Configuration (50-100 Users)
- Database connection pool: 20 connections + 10 overflow
- Rate limiting: 100 requests/minute per IP
- Redis caching for frequently accessed data
- Connection recycling every hour
- Health checks every 30 seconds

### Monitoring
- Prometheus metrics: `/metrics`
- Health check: `/health`
- Structured JSON logging
- Optional Sentry error tracking

---

## 🔒 Security

- ✅ HTTPS/TLS encryption (automatic on Render & Vercel)
- ✅ CORS with specific origins (no wildcard)
- ✅ Rate limiting (100 req/min per IP)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ JWT token authentication (30 min expiry)
- ✅ Environment variables for secrets
- ✅ Input validation with Pydantic

---

## 📝 CI/CD

GitHub Actions workflows:
- `.github/workflows/backend-ci.yml` - Backend tests & deploy
- `.github/workflows/web-admin-ci.yml` - Web build & deploy
- `.github/workflows/android-ci.yml` - Android build & test
- `.github/workflows/ios-ci.yml` - iOS build & test

Auto-deployment on push to `main` branch.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 📞 Support

- **Documentation**: See `/docs` folder
- **Issues**: Open an issue on GitHub
- **Email**: support@intellium.app

---

## 🗺️ Roadmap

### Phase 1 (Current)
- [x] Core backend API
- [x] Web admin dashboard
- [x] Mobile apps (Android/iOS)
- [x] Multi-language support
- [x] Production deployment

### Phase 2 (Next)
- [ ] Advanced AI features
- [ ] Real-time collaboration
- [ ] Advanced analytics
- [ ] Mobile offline sync
- [ ] Custom domain support

### Phase 3 (Future)
- [ ] Enterprise features
- [ ] API marketplace
- [ ] Third-party integrations
- [ ] Advanced reporting
- [ ] White-label solution

---

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT_URLS.md) - Production deployment instructions
- [Deployment Summary](DEPLOYMENT_SUMMARY.md) - Quick overview
- [i18n Guide](docs/I18N_GUIDE.md) - Internationalization setup
- [Logo Integration](docs/LOGO_INTEGRATION.md) - Branding guide
- [API Documentation](https://intellium-backend.onrender.com/docs) - Interactive API docs

---

## 🎯 Project Status

- **Backend**: ✅ Production Ready
- **Web Admin**: ✅ Production Ready
- **Mobile Apps**: ✅ Production Ready
- **Deployment**: ✅ Configured (Render + Vercel)
- **i18n**: ✅ Implemented (UZ/RU/EN)
- **CI/CD**: ✅ GitHub Actions
- **Monitoring**: ✅ Prometheus + Health Checks
- **Testing**: ⏳ In Progress

---

**Built with ❤️ by the Intellium Team**
