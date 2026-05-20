# HKAIC - AI Drone Flight Intelligence SaaS

A complete full-stack SaaS platform for drone flight log analysis with AI-powered insights.

## 🚀 Features

### Frontend
- Dark futuristic UI with cyan-purple gradient theme
- Responsive design (mobile, tablet, desktop)
- Landing page with hero, features, and CTA sections
- User dashboard with statistics
- Flight log upload interface
- Comprehensive analysis report display
- Built with Next.js 14 + Tailwind CSS + TypeScript

### Backend
- **SaaS Ready**: Multi-tenant architecture with complete data isolation
- **User Authentication**: JWT-based auth system
- **Subscription Management**: 4-tier plans (Free, Basic, Pro, Enterprise)
- **Quota Management**: Monthly analysis limits per plan
- **Log Analysis**: Comprehensive flight data analysis
- **AI Integration**: OpenAI-powered insights and recommendations
- **Multiple Formats**: CSV, ULog (PX4), Blackbox (Betaflight) support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API First**: Auto-generated Swagger/ReDoc documentation
- **Docker Ready**: Containerized deployment

## 📊 Subscription Plans

| Plan | Monthly Price | Annual Price | Monthly Quota | Max File Size | AI Analysis | Priority Support | API Access | Team Members |
|------|--------------|-------------|--------------|--------------|-------------|----------------|-----------|-------------|
| Free | $0 | $0 | 5 | 10 MB | ❌ | ❌ | ❌ | 1 |
| Basic | $9.99 | $99 | 25 | 50 MB | ✅ | ❌ | ❌ | 1 |
| Pro | $29.99 | $299 | 100 | 100 MB | ✅ | ✅ | ✅ | 3 |
| Enterprise | $99.99 | $999 | 500 | 500 MB | ✅ | ✅ | ✅ | 10 |

## 🏗️ Architecture

```
hkaic/
├── frontend/                 # Next.js frontend
│   ├── app/                  # App Router pages
│   ├── components/           # React components
│   │   ├── landing/          # Landing page components
│   │   ├── dashboard/        # Dashboard components
│   │   ├── upload/           # Upload page components
│   │   ├── report/           # Report page components
│   │   └── ui/               # UI components
│   └── package.json
│
└── backend/                  # FastAPI SaaS backend
    ├── app/
    │   ├── api/              # API endpoints
    │   │   ├── auth.py       # User auth
    │   │   ├── upload.py     # File upload
    │   │   ├── analysis.py   # Analysis endpoints
    │   │   └── health.py     # Health checks
    │   ├── auth.py           # Authentication logic
    │   ├── database.py       # DB models & setup
    │   ├── schemas.py        # Pydantic schemas
    │   ├── parsers.py        # Log parsers
    │   ├── ai_service.py     # OpenAI integration
    │   └── config.py         # Configuration
    ├── uploads/              # User uploads
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    └── README.md
```

## 🚀 Quick Start

### Option 1: Docker (All-in-one)

```bash
# Clone or navigate to project
cd hkaic/backend

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Start everything
docker-compose up -d

# Visit services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Frontend Only

```bash
# From project root
npm install
npm run dev
# Visit http://localhost:3000
```

### Option 3: Backend Only

```bash
cd backend

# Create venv and install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure and start
cp .env.example .env
python -m app.main
# API at http://localhost:8000
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/auth/register` | Register new user |
| `POST /api/auth/login` | Login and get token |
| `GET /api/subscription/plans` | Get subscription plans |
| `POST /api/upload/` | Upload flight log |
| `GET /api/upload/logs` | List user's logs |
| `POST /api/analysis/` | Analyze flight log |
| `GET /api/analysis/{log_id}` | Get analysis results |

See [backend/README.md](backend/README.md) for complete API documentation.

## 🔧 Configuration

### Backend Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```env
# Database
DATABASE_URL=sqlite:///./hkaic.db

# Optional: OpenAI for advanced AI analysis
OPENAI_API_KEY=

# Optional: Supabase integration
SUPABASE_URL=
SUPABASE_KEY=

# Security
SECRET_KEY=your-secret-key-here
```

## 📊 Analysis Features

The platform performs comprehensive analysis of drone flight logs:

### 1. Overall Flight Score
- Efficiency score
- Stability score
- Overall performance rating
- Risk level assessment

### 2. PID Tuning Analysis
- Pitch PID performance
- Roll PID performance
- Yaw PID performance
- Optimization recommendations

### 3. GPS Drift Detection
- Position accuracy analysis
- Drift pattern detection
- Problem area identification

### 4. Vibration Analysis
- Maximum vibration levels
- Average vibration
- Peak detection

### 5. Motor Anomaly Detection
- Motor performance analysis
- Unusual pattern detection
- Maintenance recommendations

### 6. AI-Powered Insights
- Automated improvement suggestions
- Safety recommendations
- Best practice guidance

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS 3
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Charts**: Recharts

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11
- **Database**: PostgreSQL / SQLite
- **ORM**: SQLAlchemy 2.0
- **Auth**: JWT (python-jose)
- **AI**: OpenAI API
- **File Parsing**: pandas + numpy
- **API Docs**: Swagger UI / ReDoc

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Cloud Storage**: Supabase / S3 (optional)

## 🔮 Future Enhancements

### SaaS Features
- [ ] Stripe payment integration
- [ ] Email verification & password reset
- [ ] Admin dashboard
- [ ] Rate limiting & DDoS protection
- [ ] Usage analytics
- [ ] Webhook support
- [ ] Team/organization management

### Analysis Features
- [ ] More log format support
- [ ] Real-time streaming analysis
- [ ] Comparative analysis between flights
- [ ] Custom alert rules
- [ ] Advanced visualization
- [ ] Machine learning models

### Infrastructure
- [ ] Kubernetes deployment configs
- [ ] CI/CD pipeline
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Log aggregation (ELK)
- [ ] Automated backups
- [ ] Multi-region deployment

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For support or questions:
1. Check the documentation in the respective READMEs
2. Open an issue in the repository
3. Contact the maintainers

---

**HKAIC - Making Drone Flight Analysis Simple and Intelligent** 🚁✨
