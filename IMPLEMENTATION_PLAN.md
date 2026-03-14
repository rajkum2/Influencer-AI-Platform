# AI Tech Influencer Discovery Platform - Implementation Plan

## Executive Summary

Building an enterprise-grade, production-ready platform for discovering, ranking, tracking, and engaging AI tech influencers across regions, technologies, and content platforms.

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Next.js 14 (App Router)  │  React Query  │  TailwindCSS  │  shadcn/ui     │
│  - SSR for SEO            │  - Caching    │  - Dark/Light │  - Components  │
│  - Real-time updates      │  - Mutations  │  - Responsive │  - Charts      │
└───────────────────────────┴───────────────┴───────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Kong/AWS API Gateway  │  Rate Limiting  │  Auth (JWT + API Keys)  │  SSL  │
└────────────────────────┴─────────────────┴─────────────────────────┴────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  FastAPI (Python)                                    │  Node.js (WebSocket)  │
│  - Influencer Service                                │  - Real-time updates  │
│  - Content Service                                   │  - Notifications      │
│  - Ranking Service                                   │                       │
│  - CRM Service                                       │                       │
│  - Admin Service                                     │                       │
└──────────────────────────────────────────────────────┴───────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WORKER LAYER (Celery + Redis)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Ingestion Workers  │  AI Processing Workers  │  Scoring Workers  │  Notif  │
│  - YouTube          │  - Topic Classification │  - Rank Calc      │  - Email│
│  - GitHub           │  - Summary Generation   │  - Trend Analysis │  - Push │
│  - RSS/Blog         │  - Embedding Generation │  - Growth Track   │  - Slack│
│  - Bluesky          │  - Entity Extraction    │                   │         │
└─────────────────────┴─────────────────────────┴───────────────────┴─────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  PostgreSQL 15     │  ClickHouse      │  Meilisearch    │  Redis          │
│  - Core entities   │  - Analytics     │  - Full-text    │  - Cache        │
│  - Relationships   │  - Time-series   │  - Faceted      │  - Sessions     │
│  - ACID compliance │  - Rank history  │  - Typo-tol     │  - Queues       │
├───────────────────┼──────────────────┼─────────────────┼───────────────────┤
│  MinIO/S3          │  Qdrant/Pinecone │  Grafana        │  Prometheus     │
│  - Thumbnails      │  - Vector Search │  - Monitoring   │  - Metrics      │
│  - Assets          │  - Similarity    │  - Alerting     │  - Alerting     │
└───────────────────┴──────────────────┴─────────────────┴───────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14, React 18, TypeScript | SSR, App Router, Type Safety |
| **Styling** | TailwindCSS, shadcn/ui | Consistent, accessible UI |
| **State** | React Query, Zustand | Server state, Client state |
| **Backend** | FastAPI, Python 3.11 | High-performance async API |
| **WebSocket** | Socket.io | Real-time updates |
| **Workers** | Celery, Redis | Background job processing |
| **Database** | PostgreSQL 15 | Primary relational store |
| **Analytics** | ClickHouse | Time-series, rankings |
| **Search** | Meilisearch | Full-text, faceted search |
| **Vector DB** | Qdrant | Similarity search, embeddings |
| **Cache** | Redis | Caching, sessions, rate limiting |
| **Storage** | MinIO (S3-compatible) | File storage |
| **Queue** | Redis + Celery | Task queuing |
| **Monitoring** | Prometheus, Grafana | Metrics, dashboards |
| **Logging** | ELK Stack / Loki | Centralized logging |
| **AI/ML** | OpenAI, HuggingFace | Classification, embeddings |
| **Testing** | Pytest, Jest, Playwright | Unit, integration, E2E |
| **CI/CD** | GitHub Actions | Automated pipelines |
| **Infra** | Docker, Docker Compose, Kubernetes | Containerization, orchestration |

---

## 2. Database Schema Design

### 2.1 Core Entities

```sql
-- ============================================
-- CORE TABLES
-- ============================================

-- Influencer Master Table
CREATE TABLE influencers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    headline VARCHAR(500),
    bio TEXT,
    
    -- Location
    country_code CHAR(2),
    region VARCHAR(50), -- North America, Europe, APAC, etc.
    city VARCHAR(100),
    timezone VARCHAR(50),
    
    -- Professional
    company VARCHAR(255),
    role_type VARCHAR(50), -- founder, researcher, educator, engineer, investor, indie
    
    -- Contact
    website_url VARCHAR(500),
    email_public VARCHAR(255),
    
    -- Media
    profile_image_url VARCHAR(500),
    
    -- Status
    verification_status VARCHAR(20) DEFAULT 'pending', -- pending, verified, rejected
    is_active BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    -- Full-text search
    search_vector TSVECTOR
);

-- Social Accounts Table
CREATE TABLE social_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    influencer_id UUID NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    
    platform VARCHAR(50) NOT NULL, -- youtube, github, twitter, linkedin, etc.
    handle VARCHAR(255),
    url VARCHAR(500) NOT NULL,
    platform_user_id VARCHAR(255),
    
    -- Metrics (cached)
    followers_count BIGINT,
    following_count BIGINT,
    post_count INTEGER,
    
    -- Platform-specific
    account_type VARCHAR(50), -- personal, business, creator
    is_verified BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT true,
    
    -- Sync tracking
    last_synced_at TIMESTAMPTZ,
    sync_status VARCHAR(20) DEFAULT 'pending', -- pending, syncing, success, error
    sync_error TEXT,
    
    -- API quota tracking
    api_calls_today INTEGER DEFAULT 0,
    api_quota_reset_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(influencer_id, platform)
);

-- Content Items Table
CREATE TABLE content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    influencer_id UUID NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    social_account_id UUID REFERENCES social_accounts(id),
    
    platform VARCHAR(50) NOT NULL,
    content_type VARCHAR(50) NOT NULL, -- video, post, article, repo, podcast
    
    -- Content
    external_id VARCHAR(255) NOT NULL,
    original_url VARCHAR(500) NOT NULL,
    title VARCHAR(500),
    body_text TEXT,
    body_html TEXT,
    
    -- Media
    thumbnail_url VARCHAR(500),
    duration_seconds INTEGER, -- for videos/podcasts
    
    -- Metadata
    published_at TIMESTAMPTZ,
    language_code CHAR(2),
    country_hint VARCHAR(2),
    
    -- AI Enrichment
    summary TEXT,
    embedding VECTOR(1536), -- OpenAI ada-002 dimensions
    
    -- Quality Signals
    quality_score DECIMAL(4,3), -- 0.000 to 1.000
    spam_score DECIMAL(4,3),
    
    -- Status
    processing_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    is_indexed BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(platform, external_id)
);

-- Content Engagement Metrics (time-series, separate for performance)
CREATE TABLE content_engagement (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    measured_at TIMESTAMPTZ DEFAULT NOW(),
    
    views BIGINT,
    likes BIGINT,
    comments BIGINT,
    shares BIGINT,
    
    -- Platform specific
    additional_metrics JSONB -- platform-specific metrics
);

-- ============================================
-- TAXONOMY TABLES
-- ============================================

-- Technology/Topic Taxonomy
CREATE TABLE technologies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id UUID REFERENCES technologies(id),
    
    -- For AI classification
    keywords TEXT[],
    embedding VECTOR(1536),
    
    -- Stats
    influencer_count INTEGER DEFAULT 0,
    content_count INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Influencer-Technology Mapping
CREATE TABLE influencer_technologies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    influencer_id UUID NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    technology_id UUID NOT NULL REFERENCES technologies(id) ON DELETE CASCADE,
    
    -- Scoring
    relevance_score DECIMAL(4,3), -- how relevant is this tech to influencer
    content_count INTEGER DEFAULT 0,
    
    -- Source
    detection_method VARCHAR(50), -- ai_classified, manual, self_reported
    confidence DECIMAL(4,3),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(influencer_id, technology_id)
);

-- Content-Technology Mapping
CREATE TABLE content_technologies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    technology_id UUID NOT NULL REFERENCES technologies(id) ON DELETE CASCADE,
    
    relevance_score DECIMAL(4,3),
    confidence DECIMAL(4,3),
    detection_method VARCHAR(50),
    
    UNIQUE(content_id, technology_id)
);

-- ============================================
-- RANKING TABLES
-- ============================================

-- Rank Snapshots (for historical tracking)
CREATE TABLE rank_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    influencer_id UUID NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Overall Scores
    overall_score DECIMAL(6,3),
    overall_rank INTEGER,
    
    -- Component Scores
    authority_score DECIMAL(6,3),
    relevance_score DECIMAL(6,3),
    quality_score DECIMAL(6,3),
    engagement_score DECIMAL(6,3),
    consistency_score DECIMAL(6,3),
    growth_score DECIMAL(6,3),
    trust_score DECIMAL(6,3),
    
    -- Context
    technology_id UUID REFERENCES technologies(id), -- null for global
    region VARCHAR(50), -- null for global
    
    -- Change tracking
    rank_change_7d INTEGER,
    rank_change_30d INTEGER,
    score_change_7d DECIMAL(6,3),
    score_change_30d DECIMAL(6,3)
);

-- Ranking Configuration (for custom formulas)
CREATE TABLE ranking_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Weights (must sum to 1.0)
    authority_weight DECIMAL(3,2) DEFAULT 0.25,
    relevance_weight DECIMAL(3,2) DEFAULT 0.20,
    quality_weight DECIMAL(3,2) DEFAULT 0.20,
    engagement_weight DECIMAL(3,2) DEFAULT 0.15,
    consistency_weight DECIMAL(3,2) DEFAULT 0.10,
    growth_weight DECIMAL(3,2) DEFAULT 0.05,
    trust_weight DECIMAL(3,2) DEFAULT 0.05,
    
    -- Filters
    technology_filter UUID REFERENCES technologies(id),
    region_filter VARCHAR(50),
    
    created_by UUID REFERENCES users(id),
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- CRM TABLES
-- ============================================

-- Relationships / CRM
CREATE TABLE influencer_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    influencer_id UUID NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES users(id),
    
    -- Pipeline
    stage VARCHAR(50) DEFAULT 'not_contacted', -- not_contacted, contacted, responded, meeting, partnered, declined
    
    -- Notes
    notes TEXT,
    
    -- Follow-up
    last_contacted_at TIMESTAMPTZ,
    next_follow_up_at TIMESTAMPTZ,
    follow_up_reminder_sent BOOLEAN DEFAULT false,
    
    -- Opportunity
    opportunity_type VARCHAR(50)[], -- speaker, advisor, sponsor, podcast, etc.
    estimated_value DECIMAL(12,2),
    
    -- Source
    source VARCHAR(100), -- how did we find them
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(influencer_id, owner_id)
);

-- Interactions Log
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    relationship_id UUID NOT NULL REFERENCES influencer_relationships(id) ON DELETE CASCADE,
    
    interaction_type VARCHAR(50) NOT NULL, -- email, dm, call, meeting, note
    direction VARCHAR(20), -- inbound, outbound
    
    -- Content
    subject VARCHAR(255),
    content TEXT,
    
    -- Metadata
    occurred_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    -- Attachments
    attachments JSONB
);

-- ============================================
-- USER & TEAM TABLES
-- ============================================

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255), -- null for SSO users
    
    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    
    -- Role
    role VARCHAR(20) DEFAULT 'member', -- superadmin, admin, member, viewer
    
    -- Team
    team_id UUID REFERENCES teams(id),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    email_verified_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    
    -- Preferences
    preferences JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Teams
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    
    -- Billing
    plan VARCHAR(20) DEFAULT 'free', -- free, starter, pro, enterprise
    
    -- Limits
    max_influencers INTEGER DEFAULT 100,
    max_team_members INTEGER DEFAULT 3,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- WATCHLIST TABLES
-- ============================================

-- Watchlists
CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    owner_id UUID NOT NULL REFERENCES users(id),
    team_id UUID REFERENCES teams(id), -- null for personal
    
    -- Sharing
    is_shared BOOLEAN DEFAULT false,
    shared_with UUID[],
    
    -- Filters (for dynamic lists)
    filter_criteria JSONB, -- stored filter config
    is_dynamic BOOLEAN DEFAULT false,
    
    -- Alerts
    alert_config JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Watchlist Members
CREATE TABLE watchlist_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watchlist_id UUID NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    influencer_id UUID NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    
    added_by UUID REFERENCES users(id),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    
    UNIQUE(watchlist_id, influencer_id)
);

-- ============================================
-- AUDIT & SYSTEM TABLES
-- ============================================

-- Audit Log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL, -- insert, update, delete
    
    old_data JSONB,
    new_data JSONB,
    
    performed_by UUID REFERENCES users(id),
    performed_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET
);

-- API Usage Tracking
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255),
    
    quota_used INTEGER,
    quota_remaining INTEGER,
    
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT
);

-- System Jobs
CREATE TABLE system_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL, -- ingest, score, classify, etc.
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed
    
    -- Payload
    payload JSONB,
    
    -- Progress
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    progress_percent INTEGER DEFAULT 0,
    
    -- Results
    result JSONB,
    error TEXT,
    
    -- Scheduling
    scheduled_for TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.2 ClickHouse Analytics Schema

```sql
-- Time-series metrics for influencer activity
CREATE TABLE influencer_metrics (
    influencer_id UUID,
    date Date,
    
    -- Followers (per platform)
    youtube_subscribers UInt64,
    github_followers UInt64,
    twitter_followers UInt64,
    total_followers UInt64,
    
    -- Content
    content_published UInt16,
    total_views UInt64,
    total_likes UInt64,
    total_comments UInt64,
    
    -- Engagement rate (calculated)
    engagement_rate Decimal(5,4),
    
    -- Scores
    overall_score Decimal(6,3),
    
    -- Partitioning
    INDEX idx_influencer_date (influencer_id, date)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (influencer_id, date);

-- Content performance
CREATE TABLE content_metrics (
    content_id UUID,
    influencer_id UUID,
    platform String,
    date Date,
    
    views UInt64,
    likes UInt64,
    comments UInt64,
    shares UInt64,
    
    INDEX idx_content_date (content_id, date)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (content_id, date);

-- Platform-wide aggregations
CREATE TABLE platform_stats (
    date Date,
    platform String,
    
    total_influencers UInt32,
    total_content UInt32,
    total_api_calls UInt32,
    quota_usage_percent Decimal(5,2)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, platform);
```

---

## 3. Implementation Phases

### Phase 0: Foundation (Weeks 1-2)

**Goal:** Infrastructure, database, authentication, and basic API structure.

**Deliverables:**
- [ ] Docker Compose setup for all services
- [ ] PostgreSQL schema + migrations
- [ ] Redis configuration
- [ ] FastAPI project structure
- [ ] Next.js project structure
- [ ] Authentication system (JWT + OAuth)
- [ ] Basic user/team management
- [ ] API documentation (OpenAPI/Swagger)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Basic monitoring setup

**Key Decisions:**
- Use Alembic for database migrations
- Implement soft deletes for all entities
- Set up structured logging from day one

---

### Phase 1: MVP Core (Weeks 3-6)

**Goal:** Working influencer directory with YouTube + GitHub + RSS ingestion.

**Deliverables:**
- [ ] Influencer CRUD API
- [ ] Social account management
- [ ] YouTube Data API connector
- [ ] GitHub API connector
- [ ] RSS/Blog crawler
- [ ] Basic content ingestion pipeline
- [ ] Search & filter API
- [ ] Dashboard UI
- [ ] Influencer Explorer UI
- [ ] Profile page UI
- [ ] Admin curation UI
- [ ] Simple ranking (followers-based)
- [ ] Watchlists (basic)

**Technical Focus:**
- YouTube quota management system
- Rate limiting for all external APIs
- Content deduplication logic
- Basic full-text search

---

### Phase 2: Intelligence Layer (Weeks 7-10)

**Goal:** AI-powered classification, ranking engine, and content intelligence.

**Deliverables:**
- [ ] Technology taxonomy system
- [ ] OpenAI integration for classification
- [ ] Topic tagging pipeline
- [ ] Content summarization
- [ ] Embedding generation & storage
- [ ] Advanced ranking algorithm
- [ ] Custom ranking formulas
- [ ] Rankings page UI
- [ ] Content Feed UI
- [ ] Meilisearch integration
- [ ] Qdrant vector search
- [ ] Bluesky connector
- [ ] Content timeline feature

**Technical Focus:**
- Async AI processing with Celery
- Embedding caching strategy
- Ranking recalculation scheduling
- Vector similarity search

---

### Phase 3: Operations & CRM (Weeks 11-14)

**Goal:** Full CRM functionality, team collaboration, and workflow automation.

**Deliverables:**
- [ ] Relationship/CRM data model
- [ ] Pipeline management
- [ ] Interaction logging
- [ ] Follow-up reminders
- [ ] Notes & attachments
- [ ] Team collaboration features
- [ ] Permission system (RBAC)
- [ ] Alerts & notifications
- [ ] Email notifications
- [ ] Weekly digest generation
- [ ] Export functionality (CSV, JSON)
- [ ] Bulk operations

**Technical Focus:**
- Notification queue system
- Email service integration
- Audit logging
- Data export security

---

### Phase 4: Scale & Advanced Features (Weeks 15-18)

**Goal:** Performance optimization, advanced analytics, and platform expansion.

**Deliverables:**
- [ ] X/Twitter API integration (if viable)
- [ ] LinkedIn connected-account flow
- [ ] ClickHouse analytics
- [ ] Advanced dashboards
- [ ] Trend analysis
- [ ] Similar influencer engine
- [ ] Compare mode
- [ ] Influence graph visualization
- [ ] Public API for customers
- [ ] Webhook system
- [ ] Advanced caching strategies
- [ ] Performance optimizations

**Technical Focus:**
- Read replicas for PostgreSQL
- CDN integration
- Advanced caching (Redis Cluster)
- Load testing & optimization

---

## 4. API Design

### 4.1 REST API Structure

```
/api/v1/
├── auth/
│   ├── POST /login
│   ├── POST /register
│   ├── POST /refresh
│   ├── POST /logout
│   └── POST /forgot-password
│
├── influencers/
│   ├── GET / (list with filters)
│   ├── POST / (create)
│   ├── GET /{id} (get one)
│   ├── PUT /{id} (update)
│   ├── DELETE /{id} (delete)
│   ├── GET /{id}/content
│   ├── GET /{id}/social-accounts
│   ├── POST /{id}/social-accounts
│   └── GET /{id}/rank-history
│
├── content/
│   ├── GET / (list with filters)
│   ├── GET /{id}
│   ├── GET /{id}/similar
│   └── POST /{id}/tag
│
├── rankings/
│   ├── GET / (current rankings)
│   ├── GET /history
│   ├── GET /configs
│   ├── POST /configs
│   └── POST /calculate (trigger recalc)
│
├── technologies/
│   ├── GET /
│   ├── GET /{id}
│   ├── GET /{id}/influencers
│   └── GET /{id}/content
│
├── watchlists/
│   ├── GET /
│   ├── POST /
│   ├── GET /{id}
│   ├── PUT /{id}
│   ├── DELETE /{id}
│   ├── POST /{id}/members
│   └── DELETE /{id}/members/{influencer_id}
│
├── crm/
│   ├── GET /relationships
│   ├── POST /relationships
│   ├── GET /relationships/{id}
│   ├── PUT /relationships/{id}
│   ├── GET /relationships/{id}/interactions
│   └── POST /relationships/{id}/interactions
│
├── admin/
│   ├── GET /queue/status
│   ├── POST /queue/trigger
│   ├── GET /audit-logs
│   ├── GET /system-jobs
│   └── POST /influencers/bulk-import
│
└── me/
    ├── GET /profile
    ├── PUT /profile
    ├── GET /preferences
    ├── PUT /preferences
    └── GET /notifications
```

### 4.2 WebSocket Events

```javascript
// Real-time updates
influencer:updated      // When influencer data changes
content:new            // New content published
ranking:changed        // Ranking recalculated
notification:new       // New notification
job:progress           // Background job progress
```

---

## 5. Frontend Architecture

### 5.1 Directory Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/
│   │   ├── login/
│   │   ├── register/
│   │   └── forgot-password/
│   ├── (dashboard)/
│   │   ├── page.tsx             # Dashboard
│   │   ├── influencers/
│   │   │   ├── page.tsx         # Explorer
│   │   │   └── [id]/
│   │   │       └── page.tsx     # Profile
│   │   ├── content/
│   │   ├── rankings/
│   │   ├── watchlists/
│   │   ├── crm/
│   │   └── admin/
│   ├── api/                     # API routes (auth, etc.)
│   └── layout.tsx
│
├── components/
│   ├── ui/                      # shadcn/ui components
│   ├── layout/                  # Layout components
│   ├── influencers/             # Influencer-specific
│   ├── content/                 # Content-specific
│   ├── filters/                 # Filter components
│   ├── charts/                  # Data visualization
│   └── forms/                   # Form components
│
├── lib/
│   ├── api/                     # API clients
│   ├── hooks/                   # Custom React hooks
│   ├── stores/                  # Zustand stores
│   ├── utils/                   # Utilities
│   └── constants/               # Constants
│
├── types/                       # TypeScript types
├── styles/                      # Global styles
└── public/                      # Static assets
```

### 5.2 State Management

```typescript
// Zustand stores
useAuthStore      // Authentication state
useInfluencerStore // Influencer data
useFilterStore    // Global filters
useUIStore        // UI state (sidebar, modals, etc.)

// React Query
// - Server state caching
// - Optimistic updates
// - Background refetching
```

---

## 6. Security Considerations

### 6.1 Authentication & Authorization
- JWT with refresh token rotation
- OAuth 2.0 for social logins
- API key authentication for service-to-service
- Role-based access control (RBAC)
- Resource-level permissions

### 6.2 Data Protection
- Encryption at rest (PostgreSQL TDE)
- TLS 1.3 in transit
- PII data masking in logs
- GDPR compliance (data export, deletion)
- Rate limiting per user/IP

### 6.3 API Security
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy)
- XSS protection
- CSRF tokens
- API rate limiting

---

## 7. Monitoring & Observability

### 7.1 Metrics
- Request latency (p50, p95, p99)
- Error rates
- API quota usage by platform
- Queue depth and processing time
- Database connection pool
- Cache hit/miss rates

### 7.2 Logging
- Structured JSON logging
- Correlation IDs for request tracing
- Sensitive data redaction
- Log retention policies

### 7.3 Alerting
- High error rates
- Queue backlog
- API quota exhaustion
- Database connection issues
- Infrastructure health

---

## 8. Deployment Architecture

### 8.1 Development
```bash
# Local development with Docker Compose
docker-compose -f docker-compose.dev.yml up

# Includes:
# - PostgreSQL
# - Redis
# - Meilisearch
# - Qdrant
# - MinIO
# - Backend (hot reload)
# - Frontend (hot reload)
```

### 8.2 Production
- Kubernetes cluster (EKS/GKE)
- Managed PostgreSQL (RDS/Cloud SQL)
- Managed Redis (ElastiCache/Memorystore)
- CDN for static assets
- Load balancer with SSL termination
- Auto-scaling based on CPU/memory

---

## 9. Testing Strategy

### 9.1 Backend
- Unit tests (Pytest) - 80%+ coverage
- Integration tests for API endpoints
- Database migration tests
- Worker task tests

### 9.2 Frontend
- Unit tests (Jest + React Testing Library)
- Component tests
- E2E tests (Playwright)
- Visual regression tests

### 9.3 Infrastructure
- Load testing (k6)
- Chaos engineering
- Security scanning

---

## 10. Success Metrics

| Metric | Target (3 months) |
|--------|-------------------|
| Influencer Coverage | 10,000 profiles |
| Content Freshness | < 7 days median |
| API Uptime | 99.9% |
| Search Response Time | < 100ms (p95) |
| Page Load Time | < 2s |
| User Signups | 500 teams |

---

## Appendix: Technology Classifications

### Primary Technologies
1. LLMs & Foundation Models
2. AI Agents & Agent Frameworks
3. RAG (Retrieval-Augmented Generation)
4. Vector Databases
5. AI Infrastructure & MLOps
6. AI Coding & Dev Tools
7. Multimodal AI
8. Voice AI & Speech
9. Computer Vision
10. Robotics & Embodied AI
11. Fine-tuning & Training
12. Evaluation & Benchmarking
13. GPU/Cloud AI
14. AI Product Management
15. AI Marketing & Growth
16. AI Healthcare
17. AI Finance
18. MCP (Model Context Protocol)
19. AI Safety & Alignment
20. Open Source AI

### Domain Classifications
1. Research
2. Engineering
3. Startup Founder
4. Infrastructure
5. Product Management
6. Developer Relations
7. Education
8. Venture Capital
9. Open Source Contributor
10. Indie Hacker
