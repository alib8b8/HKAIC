# HKAIC Backend - FastAPI SaaS

FastAPI SaaS backend for HKAIC - AI Drone Flight Intelligence Platform with multi-tenant architecture, user authentication, and subscription management.

## Features

### SaaS Features
- **User Authentication**: JWT-based authentication system
- **Multi-tenant Architecture**: Complete data isolation between users
- **Subscription Plans**: 4 tiers (Free, Basic, Pro, Enterprise) with varying quotas and features
- **Quota Management**: Monthly analysis limits per subscription tier
- **Role-based Access**: User, Admin, and Superadmin roles

### Core Features
- **File Upload API**: Upload and manage drone flight logs
- **Multiple Log Formats**: Support for .csv, .ulg (PX4), and .bbl (Betaflight)
- **AI-powered Analysis**: OpenAI integration for intelligent insights
- **Comprehensive Analysis**:
  - Flight score calculation
  - PID tuning analysis
  - GPS drift detection
  - Vibration analysis
  - Motor anomaly detection
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Supabase Integration**: Optional cloud storage
- **API Documentation**: Auto-generated Swagger/ReDoc

## Subscription Plans

| Plan | Monthly Price | Annual Price | Monthly Quota | Max File Size | AI Analysis | Priority Support | API Access | Team Members |
|------|--------------|-------------|--------------|--------------|-------------|----------------|-----------|-------------|
| Free | $0 | $0 | 5 | 10 MB | ❌ | ❌ | ❌ | 1 |
| Basic | $9.99 | $99 | 25 | 50 MB | ✅ | ❌ | ❌ | 1 |
| Pro | $29.99 | $299 | 100 | 100 MB | ✅ | ✅ | ✅ | 3 |
| Enterprise | $99.99 | $999 | 500 | 500 MB | ✅ | ✅ | ✅ | 10 |

## Quick Start

### Development (Local)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run with script
./start.sh

# Or run directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
cd backend

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Environment
ENVIRONMENT=development

# Database (SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite:///./hkaic.db
# DATABASE_URL=postgresql://user:password@localhost:5432/hkaic

# Supabase (Optional)
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# OpenAI (Optional, enables advanced AI analysis)
OPENAI_API_KEY=your-openai-api-key

# Security (Change in production!)
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/auth/register` | POST | Register a new user | ❌ |
| `/api/auth/login` | POST | Login and get token | ❌ |
| `/api/auth/me` | GET | Get current user profile | ✅ |

### Subscription
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/subscription/plans` | GET | Get all subscription plans | ❌ |
| `/api/subscription/my-plan` | GET | Get current user's plan | ✅ |

### Upload
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/upload/` | POST | Upload flight log | ✅ |
| `/api/upload/logs` | GET | List user's logs | ✅ |
| `/api/upload/logs/{id}` | GET | Get log details | ✅ |
| `/api/upload/logs/{id}` | DELETE | Delete log | ✅ |

### Analysis
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/analysis/` | POST | Analyze flight log | ✅ |
| `/api/analysis/{log_id}` | GET | Get analysis results | ✅ |
| `/api/analysis/score/{log_id}` | GET | Get flight scores | ✅ |
| `/api/analysis/recommendations/{log_id}` | GET | Get recommendations | ✅ |
| `/api/analysis/pid/{log_id}` | GET | Get PID analysis | ✅ |
| `/api/analysis/vibration/{log_id}` | GET | Get vibration analysis | ✅ |
| `/api/analysis/gps/{log_id}` | GET | Get GPS drift analysis | ✅ |
| `/api/analysis/motors/{log_id}` | GET | Get motor analysis | ✅ |
| `/api/analysis/re-analyze/{log_id}` | POST | Re-run analysis | ✅ |

## Usage Examples

### Python

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Register user
register_data = {
    "email": "user@example.com",
    "username": "droneuser",
    "password": "securepassword"
}
response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)

# 2. Login
login_data = {
    "email": "user@example.com",
    "password": "securepassword"
}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 3. Upload log
with open("flight_log.csv", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/api/upload/",
        files=files,
        headers=headers
    )
log_id = response.json()["id"]

# 4. Analyze
analysis_data = {"flight_log_id": log_id}
response = requests.post(
    f"{BASE_URL}/api/analysis/",
    json=analysis_data,
    headers=headers
)
analysis = response.json()
print(f"Overall Score: {analysis['overall_score']}")
```

### JavaScript (Fetch)

```javascript
const BASE_URL = "http://localhost:8000";

// Register
const register = async () => {
  const response = await fetch(`${BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: "user@example.com",
      username: "droneuser",
      password: "securepassword"
    })
  });
  return response.json();
};

// Login
const login = async (email, password) => {
  const response = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const { access_token } = await response.json();
  return access_token;
};

// Upload and analyze
const processLog = async (file, token) => {
  const headers = { "Authorization": `Bearer ${token}` };
  
  // Upload
  const formData = new FormData();
  formData.append("file", file);
  const uploadRes = await fetch(`${BASE_URL}/api/upload/`, {
    method: "POST",
    headers,
    body: formData
  });
  const { id } = await uploadRes.json();
  
  // Analyze
  const analysisRes = await fetch(`${BASE_URL}/api/analysis/`, {
    method: "POST",
    headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify({ flight_log_id: id })
  });
  return analysisRes.json();
};
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration
│   ├── database.py          # DB models & setup
│   ├── auth.py              # Authentication logic
│   ├── schemas.py           # Pydantic schemas
│   ├── parsers.py           # Log file parsers
│   ├── ai_service.py        # OpenAI integration
│   ├── supabase_service.py  # Supabase integration
│   └── api/
│       ├── __init__.py
│       ├── health.py        # Health endpoints
│       ├── auth.py          # Auth endpoints
│       ├── upload.py        # Upload endpoints
│       └── analysis.py      # Analysis endpoints
├── uploads/                 # User uploaded files
├── requirements.txt         # Python dependencies
├── .env.example             # Example env config
├── .env                     # Actual env config
├── Dockerfile               # Docker config
├── docker-compose.yml       # Docker Compose config
├── start.sh                 # Start script
└── README.md
```

## Development

### Database Migrations

Uses SQLAlchemy's metadata create_all. For production, consider using Alembic.

### Testing

```bash
# Run tests (placeholder for real tests)
python -m pytest
```

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs

## Production Deployment

### Recommended Stack
- **Server**: Docker or Kubernetes
- **Database**: PostgreSQL
- **File Storage**: AWS S3 or Supabase Storage
- **Reverse Proxy**: Nginx or Traefik
- **SSL**: Let's Encrypt with Certbot
- **Monitoring**: Prometheus + Grafana

### Environment Checklist

- [ ] Use PostgreSQL in production
- [ ] Set secure SECRET_KEY
- [ ] Configure proper CORS origins
- [ ] Set up HTTPS
- [ ] Enable rate limiting
- [ ] Set up logging/monitoring
- [ ] Configure backup strategy
- [ ] Set up Stripe for payments (optional)

## Next Steps for SaaS

- [ ] Implement Stripe payment integration
- [ ] Add email verification & password reset
- [ ] Create admin dashboard UI
- [ ] Add rate limiting
- [ ] Implement audit logging
- [ ] Add team/organization management
- [ ] Implement usage analytics
- [ ] Add webhook support

## License

MIT License
