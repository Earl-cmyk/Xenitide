# Xenitide - Student All-in-One Development Platform

A comprehensive development platform designed for students, offering project management, code repositories, database management, deployments, and payment processing - all in one place.

## 🚀 Features

### Core Features
- **Project Management**: Create and manage multiple projects with team collaboration
- **Code Repository**: Git-like version control with file management
- **Database Management**: Visual database editor with table and row management
- **Deployments**: One-click deployment to various platforms
- **Payment Processing**: Integrated Xendit payment links for donations
- **AI Assistant**: Built-in AI code review and suggestions
- **Real-time Logs**: Live build logs and system monitoring

### Subscription Tiers
- **Free Tier**: 5 projects, 100 AI actions/month, 100MB storage
- **Premium Tier**: 50 projects, unlimited AI actions, unlimited storage

## 🏗️ Architecture

### Frontend
- **HTML5/CSS3/JavaScript**: Modern responsive web interface
- **Component-based**: Modular design for maintainability
- **Real-time Updates**: Live status updates and notifications

### Backend
- **FastAPI**: Modern Python web framework
- **Supabase**: PostgreSQL database and authentication
- **Xendit**: Payment processing and donations
- **JWT Authentication**: Secure user authentication

### Database
- **PostgreSQL**: Robust relational database
- **Supabase**: Managed database service
- **Real-time Subscriptions**: Live data updates

## 📋 Prerequisites

- Python 3.11+
- Node.js 16+ (for frontend development)
- Supabase account
- Xendit account (for payments)

## 🛠️ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Earl-cmyk/Xenitide.git
cd Xenitide
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your actual values
nano .env
```

### 3. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Start the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup
```bash
# Serve the frontend (you can use any static server)
python -m http.server 3000
# or
npx serve .
```

### 5. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🔧 Configuration

### Required Environment Variables
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Database
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres

# Security
JWT_SECRET_KEY=your-secure-random-secret-key

# Xendit Payments
XENDIT_SECRET_KEY=your_xendit_secret_key
XENDIT_PUBLIC_KEY=your_xendit_public_key
XENDIT_DONATION_LINK=https://checkout-staging.xendit.co/donation/Maker
```

See [ENV_SETUP.md](./ENV_SETUP.md) for complete configuration guide.

## 📚 Documentation

- [API Specification](./API_SPECIFICATION.md) - Complete API documentation
- [Database Schema](./DATABASE_SCHEMA.md) - Database structure and relationships
- [Backend Integration](./BACKEND_INTEGRATION.md) - Backend service details
- [Environment Setup](./ENV_SETUP.md) - Detailed configuration guide
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment instructions

## 🚀 Deployment

### Vercel (Frontend)
```bash
npm i -g vercel
vercel --prod
```

### Supabase (Backend & Database)
```bash
npm i -g supabase
supabase login
supabase link --project-ref your-project-ref
supabase functions deploy
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment instructions.

## 🔒 Security Features

- **Environment Variables**: All secrets stored securely
- **JWT Authentication**: Secure user sessions
- **CORS Protection**: Cross-origin request security
- **Input Validation**: Comprehensive data validation
- **SQL Injection Protection**: Parameterized queries
- **Rate Limiting**: API abuse prevention

## 💳 Payment Integration

### Xendit Integration
- **Donation Links**: Easy payment collection
- **Webhook Support**: Real-time payment notifications
- **Link Expiry Monitoring**: Automatic renewal reminders
- **Secure Processing**: PCI-compliant payment handling

### Subscription Management
- **Tier-based Limits**: Automatic project limit enforcement
- **Upgrade Flow**: Seamless premium subscription process
- **Usage Tracking**: Real-time resource monitoring

## 🎯 Use Cases

### For Students
- **Project Portfolios**: Showcase academic projects
- **Team Collaboration**: Work on group assignments
- **Learning Platform**: Practice development skills
- **Deployment**: Share projects with the world

### For Educators
- **Class Management**: Organize student projects
- **Code Review**: Built-in code review tools
- **Progress Tracking**: Monitor student progress
- **Resource Sharing**: Distribute learning materials

## 🔧 Development

### Project Structure
```
Xenitide/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── db/             # Database client
│   │   ├── services/       # Business logic
│   │   └── models/         # Data models
│   └── requirements.txt    # Python dependencies
├── index.html              # Frontend application
├── script.js              # Frontend JavaScript
├── styles.css             # Frontend styling
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
└── docs/                  # Documentation
```

### API Endpoints
- **Authentication**: `/api/v1/auth/*`
- **Projects**: `/api/v1/projects/*`
- **Repositories**: `/api/v1/repos/*`
- **Deployments**: `/api/v1/deploy/*`
- **Payments**: `/api/v1/payments/*`

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest
```

### Frontend Tests
```bash
# Run frontend tests (if configured)
npm test
```

## 📊 Monitoring

### Health Checks
- **Application**: `/health`
- **Database**: Connection status monitoring
- **Payment Links**: Expiry tracking

### Logging
- **Application Logs**: Comprehensive request/response logging
- **Error Tracking**: Detailed error reporting
- **Performance Metrics**: Response time monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` folder
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join our GitHub Discussions

## 🔮 Roadmap

### Upcoming Features
- [ ] Mobile application
- [ ] Advanced AI features
- [ ] More deployment targets
- [ ] Enhanced collaboration tools
- [ ] Custom themes
- [ ] Plugin system

### Version History
- **v1.0.0**: Initial release with core features
- **v1.1.0**: Subscription system and payment integration
- **v1.2.0**: Enhanced AI assistant and collaboration tools

---

**Built with ❤️ for students and educators**
