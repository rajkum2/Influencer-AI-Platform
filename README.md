# AI Tech Influencer Discovery Platform

A comprehensive, enterprise-grade platform for discovering, ranking, tracking, and engaging AI tech influencers across regions, technologies, and content platforms.

![Platform Architecture](docs/architecture.png)

## 🚀 Features

### Core Platform
- **Influencer Directory** - Comprehensive profiles with social links, bios, and metrics
- **Content Aggregation** - Unified timeline from YouTube, GitHub, Blogs, Newsletters
- **AI-Powered Classification** - Automatic topic tagging and content summarization
- **Custom Rankings** - Weighted scoring with customizable formulas
- **CRM Integration** - Pipeline management, follow-ups, and interaction tracking
- **Watchlists** - Save and monitor specific influencers with alerts

### Platform Integrations
| Platform | Status | Features |
|----------|--------|----------|
| YouTube | ✅ Active | Channels, videos, metrics |
| GitHub | ✅ Active | Repos, activity, stars |
| Bluesky | ✅ Active | Posts, profiles |
| RSS/Blogs | ✅ Active | Articles, newsletters |
| LinkedIn | ⚠️ Limited | Requires connected accounts |
| X/Twitter | ⚠️ Limited | API cost prohibitive |

### Technology Stack

**Backend:**
- FastAPI (Python) - High-performance async API
- PostgreSQL + pgvector - Relational DB with vector support
- Redis - Caching, sessions, task queue
- Celery - Background job processing
- MeiliSearch - Full-text search
- Qdrant - Vector similarity search
- ClickHouse - Time-series analytics

**Frontend:**
- Next.js 14 - React framework with SSR
- TailwindCSS - Utility-first styling
- shadcn/ui - Component library
- TanStack Query - Server state management

**Infrastructure:**
- Docker & Docker Compose
- Kubernetes - Container orchestration
- Prometheus & Grafana - Monitoring
- MinIO - S3-compatible object storage

## 📁 Project Structure

```
Influencers-Hub-Platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── workers/        # Celery tasks
│   │   ├── connectors/     # Platform APIs
│   │   └── ai/             # AI classification
│   ├── alembic/            # Database migrations
│   └── tests/              # Test suite
├── frontend/               # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # React components
│   └── lib/               # Utilities, hooks, API
├── infra/                 # Infrastructure configs
│   ├── k8s/              # Kubernetes manifests
│   └── monitoring/       # Prometheus & Grafana
└── scripts/              # Utility scripts
```

## 🛠️ Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd Influencers-Hub-Platform

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required: YOUTUBE_API_KEY, OPENAI_API_KEY
# Optional: GITHUB_TOKEN, ANTHROPIC_API_KEY
```

### 2. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 3. Seed Database

```bash
# Run seeding script
docker-compose exec backend python -m alembic.seed_data
```

### 4. Access the Platform

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| API Docs | http://localhost:8000/docs | - |
| Flower | http://localhost:5555 | admin/admin |
| Grafana | http://localhost:3001 | admin/admin |

**Default Login:**
- Email: `admin@influencer-platform.com`
- Password: `admin123`

## 📊 API Overview

### Authentication
```bash
# Login
POST /api/v1/auth/login/json
{
  "email": "admin@influencer-platform.com",
  "password": "admin123"
}
```

### Influencers
```bash
# List influencers
GET /api/v1/influencers?page=1&page_size=20

# Search influencers
GET /api/v1/influencers/search?query=openai

# Get influencer details
GET /api/v1/influencers/{id}

# Get influencer content
GET /api/v1/influencers/{id}/content
```

### Content
```bash
# List content
GET /api/v1/content?platform=youtube&technology_id=xxx

# Get content feed
GET /api/v1/content/feed?days=7
```

### Rankings
```bash
# Get rankings
GET /api/v1/rankings?technology_id=xxx&region=Europe

# Create custom ranking config
POST /api/v1/rankings/configs
{
  "name": "AI Agents Focus",
  "authority_weight": 0.2,
  "relevance_weight": 0.35,
  ...
}
```

## 🏗️ Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload

# Run tests
pytest
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Type checking
npm run type-check
```

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (EKS, GKE, or local)
- kubectl configured
- cert-manager for SSL
- NGINX Ingress Controller

### Deploy

```bash
# Apply namespace
kubectl apply -f infra/k8s/namespace.yaml

# Create secrets
kubectl create secret generic backend-secrets \
  --from-literal=DATABASE_URL=postgresql://... \
  --from-literal=SECRET_KEY=... \
  --from-literal=OPENAI_API_KEY=... \
  -n influencer-platform

# Apply configurations
kubectl apply -f infra/k8s/

# Check status
kubectl get pods -n influencer-platform
```

## 📈 Monitoring

### Metrics Available
- API request latency and error rates
- Database connection pool status
- Celery task queue depth
- Platform API quota usage
- Influencer/content counts

### Alerts
- High error rate (>5%)
- Queue backlog (>1000 tasks)
- API quota exhaustion
- Database connection issues

## 🔒 Security

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- API rate limiting
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Audit logging

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs) - OpenAPI/Swagger
- [Architecture](IMPLEMENTATION_PLAN.md) - Detailed implementation plan
- [Deployment Guide](docs/deployment.md) - Production deployment

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for ORM
- Next.js team for the React framework
- shadcn/ui for beautiful components
