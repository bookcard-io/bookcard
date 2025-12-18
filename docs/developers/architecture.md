# Architecture

This document describes the architecture of Bookcard.

## Overview

Bookcard is built with a modern, layered architecture:

- **Frontend**: Next.js React application
- **Backend**: FastAPI Python application
- **Database**: PostgreSQL (or SQLite for development)
- **Task Queue**: Redis + Dramatiq for background jobs

## System Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Next.js    │ ◄─── Frontend (React/TypeScript)
│  Frontend   │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│   FastAPI   │ ◄─── Backend (Python)
│   Backend   │
└──────┬──────┘
       │
       ├──► PostgreSQL/SQLite
       ├──► Redis (tasks)
       └──► Calibre Library (filesystem)
```

## Backend Architecture

### Layers

1. **API Layer** (`bookcard/api/`)
    - Route handlers
    - Request/response validation
    - Authentication/authorization

2. **Service Layer** (`bookcard/services/`)
    - Business logic
    - Orchestration
    - Transaction management

3. **Repository Layer** (`bookcard/repositories/`)
    - Data access
    - Database queries
    - File operations

4. **Model Layer** (`bookcard/models/`)
    - SQLModel database models
    - Pydantic schemas
    - Domain entities

### Key Principles

- **Dependency Injection**: Services and repositories injected via FastAPI dependencies
- **Separation of Concerns**: Clear boundaries between layers
- **SOLID Principles**: Single responsibility, dependency inversion
- **IOC (Inversion of Control)**: Dependencies provided, not created

## Frontend Architecture

- **Next.js App Router**: Modern React framework
- **Server Components**: For data fetching and SEO
- **Client Components**: For interactivity
- **API Routes**: Proxy to backend API

## Data Flow

1. User action in browser
2. Frontend makes API request
3. FastAPI route handler receives request
4. Service layer processes business logic
5. Repository layer accesses data
6. Response flows back through layers

## Background Tasks

Long-running operations (library scanning, conversions) use:

- **Dramatiq**: Task queue library
- **Redis**: Message broker
- **Workers**: Separate processes for task execution

## Security

- **JWT Authentication**: Stateless token-based auth
- **OIDC Support**: Enterprise SSO integration
- **RBAC**: Role-based access control
- **Input Validation**: Pydantic schemas for all inputs
