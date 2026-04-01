# Xenitide Backend API

A FastAPI-based backend for the Xenitide student all-in-one development platform, providing project management, repository handling, deployment automation, and payment processing capabilities.

## 🚀 Features

- **Authentication & Authorization**: JWT-based auth with Supabase integration
- **Project Management**: Multi-project support with role-based permissions
- **Repository System**: Git-like repository management with file operations
- **Deployment Automation**: CI/CD simulation with build logs and status tracking
- **Payment Processing**: Xendit integration for payment links and transactions
- **Database Builder**: Flexible JSON-based database table management
- **Storage System**: File upload and management via Supabase Storage
- **Real-time Updates**: WebSocket support for live deployment logs
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## 📋 Tech Stack

- **Framework**: FastAPI
- **Database/Auth**: Supabase (PostgreSQL + Auth)
- **Payments**: Xendit
- **Language**: Python 3.11+
- **Deployment**: Docker ready

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- Supabase account and project
- Xendit account (for payments)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd xenitide/backend
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key

# Xendit (optional)
XENDIT_SECRET_KEY=your-xendit-secret-key
XENDIT_PUBLIC_KEY=your-xendit-public-key
```

### 4. Database Setup

Run the Supabase SQL setup script from the main project:

1. Go to your Supabase project SQL Editor
2. Execute the `SUPABASE_SETUP.sql` script
3. Verify all tables are created

### 5. Start the Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📁 Project Structure

```
backend/
│
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py           # Application configuration
│   │   └── security.py         # JWT and authentication utilities
│   ├── db/
│   │   └── client.py           # Supabase client wrapper
│   ├── models/
│   │   ├── user.py             # User data models
│   │   ├── project.py          # Project data models
│   │   ├── repo.py             # Repository data models
│   │   ├── deployment.py       # Deployment data models
│   │   ├── payment.py          # Payment data models
│   │   └── database.py         # Database builder models
│   ├── schemas/
│   │   ├── auth.py             # Request/response schemas
│   │   ├── project.py          # Project schemas
│   │   ├── repo.py             # Repository schemas
│   │   ├── deployment.py       # Deployment schemas
│   │   └── payment.py          # Payment schemas
│   ├── services/
│   │   ├── auth_service.py     # Authentication business logic
│   │   ├── project_service.py  # Project management logic
│   │   ├── repo_service.py     # Repository management logic
│   │   ├── deploy_service.py   # Deployment automation logic
│   │   └── payment_service.py  # Payment processing logic
│   └── api/
│       ├── deps.py             # FastAPI dependencies
│       └── routes/
│           ├── auth.py         # Authentication endpoints
│           ├── projects.py     # Project management endpoints
│           ├── repos.py        # Repository endpoints
│           ├── deploy.py       # Deployment endpoints
│           └── payments.py      # Payment endpoints
├── requirements.txt            # Python dependencies
├── Dockerfile                 # Docker configuration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🔐 Authentication

The API uses JWT tokens for authentication. Users can authenticate via:

1. **Email/Password**: Traditional signup/login
2. **Supabase Auth**: Leverages Supabase's authentication system
3. **API Keys**: For programmatic access

### Authentication Flow

```bash
# Sign up
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

## 📊 API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🚢 Deployment

### Docker Deployment

```bash
# Build image
docker build -t xenitide-backend .

# Run container
docker run -p 8000:8000 --env-file .env xenitide-backend
```

### Production Deployment

1. Set environment variables
2. Use a production ASGI server (Gunicorn/Uvicorn)
3. Configure reverse proxy (Nginx)
4. Set up SSL/TLS
5. Configure monitoring and logging

```bash
# Production with Gunicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_KEY` | Supabase anon key | ✅ |
| `JWT_SECRET_KEY` | JWT signing secret | ✅ |
| `XENDIT_SECRET_KEY` | Xendit secret key | ❌ (optional) |
| `DEBUG` | Debug mode | ❌ (default: false) |

### Supabase Setup

1. Create a new Supabase project
2. Run the SQL setup script
3. Configure authentication providers
4. Set up storage buckets
5. Configure RLS policies

### Xendit Setup (Optional)

1. Create Xendit account
2. Get API keys from dashboard
3. Configure webhook endpoints
4. Set up payment methods

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## 📝 API Usage Examples

### Create Project

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "description": "A test project"}'
```

### Create Repository

```bash
curl -X POST "http://localhost:8000/api/v1/repos" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "main-repo", "project_id": "PROJECT_ID"}'
```

### Create Deployment

```bash
curl -X POST "http://localhost:8000/api/v1/deploy" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "PROJECT_ID", "branch": "main"}'
```

### Create Payment Link

```bash
curl -X POST "http://localhost:8000/api/v1/payments/links" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "PROJECT_ID", "amount": 500.00, "description": "Product purchase"}'
```

## 🔍 Monitoring & Logging

### Health Check

```bash
curl http://localhost:8000/health
```

### Logging

The application uses structured logging with different levels:

- `INFO`: General application flow
- `WARNING`: Unexpected behavior
- `ERROR`: Error conditions
- `DEBUG`: Detailed debugging info

### Metrics

Monitor key metrics:

- Request response times
- Error rates
- Database connection health
- Authentication success/failure rates

## 🛡️ Security

### Authentication Security

- JWT tokens with configurable expiration
- Secure password hashing with bcrypt
- Rate limiting on authentication endpoints
- CORS configuration for cross-origin requests

### Data Security

- Row Level Security (RLS) in Supabase
- Environment variable encryption
- Input validation and sanitization
- SQL injection prevention

### API Security

- Request rate limiting
- Input size limits
- HTTPS enforcement in production
- API key authentication for programmatic access

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Backend
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
      - name: Deploy to production
        run: # deployment script
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the main project LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the API documentation at `/docs`
2. Review the health check endpoint status
3. Check application logs
4. Create an issue in the repository

## 🗺️ Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Advanced analytics and reporting
- [ ] Multi-region deployment support
- [ ] Advanced CI/CD integrations
- [ ] GraphQL API support
- [ ] Advanced monitoring and alerting
