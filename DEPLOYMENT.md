# Xenitide Deployment Guide

## GitHub Repository Setup

### 1. Initialize Git Repository
```bash
git init
git add .
git commit -m "Initial commit: Xenitide platform"
```

### 2. Add Remote Repository
```bash
git remote add origin https://github.com/Earl-cmyk/Xenitide.git
git branch -M main
git push -u origin main
```

### 3. Environment Variables for GitHub
- **Never commit `.env` file** (already in `.gitignore`)
- Use GitHub Secrets for CI/CD:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `XENDIT_SECRET_KEY`
  - `JWT_SECRET_KEY`

## Vercel Deployment (Frontend)

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Deploy Frontend
```bash
vercel --prod
```

### 3. Vercel Environment Variables
Set these in Vercel Dashboard → Settings → Environment Variables:

**Frontend Variables (Public):**
- `NEXT_PUBLIC_SUPABASE_URL=https://db.znbnhdozyxzbewndpxbf.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key`
- `NEXT_PUBLIC_XENDIT_PUBLIC_KEY=your_xendit_public_key`
- `NEXT_PUBLIC_XENDIT_DONATION_LINK=https://checkout-staging.xendit.co/donation/Maker`

### 4. Vercel Configuration
Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "index.html",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

## Supabase Deployment (Backend & Database)

### 1. Database Setup
```sql
-- Run the provided SUPABASE_SETUP.sql in your Supabase SQL Editor
```

### 2. Supabase Environment Variables
Set these in Supabase Dashboard → Settings → Environment Variables:

**Backend Variables:**
- `SUPABASE_URL=https://db.znbnhdozyxzbewndpxbf.supabase.co`
- `SUPABASE_KEY=your_supabase_anon_key`
- `SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key`
- `DATABASE_URL=postgresql://postgres:passwordsogoodyoucantguessit@db.znbnhdozyxzbewndpxbf.supabase.co:5432/postgres`
- `JWT_SECRET_KEY=your_secure_jwt_secret`
- `XENDIT_SECRET_KEY=your_xendit_secret_key`
- `XENDIT_PUBLIC_KEY=your_xendit_public_key`
- `XENDIT_WEBHOOK_TOKEN=your_webhook_token`

### 3. Deploy Backend to Supabase Edge Functions
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Deploy functions
supabase functions deploy
```

## Xendit Payment Integration

### 1. Xendit Account Setup
1. Sign up at [Xendit Dashboard](https://dashboard.xendit.co/)
2. Get your API keys from Settings → API Keys
3. Create donation link from Payments → Donation Links

### 2. Configure Webhook
Set webhook URL in Xendit dashboard:
```
https://your-domain.vercel.app/api/webhooks/xendit
```

### 3. Link Renewal Process
The system automatically monitors link expiry:
- **Warning**: 5 days before expiry
- **Critical**: When expired
- **Console notifications**: Displayed on server start

**To renew link:**
1. Generate new link in Xendit dashboard
2. Update `XENDIT_DONATION_LINK` in environment variables
3. Restart application

## CI/CD Pipeline (GitHub Actions)

### 1. Create `.github/workflows/deploy.yml`
```yaml
name: Deploy Xenitide

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          
      - name: Run tests
        run: |
          cd backend
          python -m pytest

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Supabase
        uses: supabase/setup-cli@v1
        with:
          version: latest
          
      - name: Deploy functions
        run: |
          supabase login --token ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          supabase functions deploy
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

### 2. GitHub Secrets Required
Set these in GitHub Repository → Settings → Secrets:
- `VERCEL_TOKEN`
- `ORG_ID` 
- `PROJECT_ID`
- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `XENDIT_SECRET_KEY`

## Security Checklist

### ✅ Before Deployment
- [ ] All API keys are in environment variables
- [ ] `.env` is in `.gitignore`
- [ ] HTTPS is enabled in production
- [ ] CORS is properly configured
- [ ] JWT secret is strong and unique
- [ ] Database connection uses SSL

### ✅ After Deployment
- [ ] Test all API endpoints
- [ ] Verify payment flow works
- [ ] Check subscription limits
- [ ] Monitor Xendit link expiry
- [ ] Set up logging and monitoring

## Monitoring and Maintenance

### 1. Health Checks
- Frontend: `https://your-domain.vercel.app/`
- Backend: `https://your-backend.supabase.co/health`
- Database: Check Supabase dashboard

### 2. Log Monitoring
```bash
# View application logs
supabase functions logs

# View Vercel logs
vercel logs
```

### 3. Backup Strategy
- Database: Supabase automatic backups
- Code: Git version control
- Environment: Store secrets securely

## Troubleshooting

### Common Issues

**1. CORS Errors**
```env
# Add your domain to CORS origins
BACKEND_CORS_ORIGINS=["https://your-domain.vercel.app"]
```

**2. Database Connection**
```env
# Verify database URL format
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres
```

**3. Xendit Link Expired**
- Check console for expiry warnings
- Update `XENDIT_DONATION_LINK` environment variable
- Restart application

**4. Subscription Limits**
- Free tier: 5 projects per user
- Premium tier: 50 projects per user
- Check `subscription_service.py` for logic

## Performance Optimization

### 1. Frontend
- Enable Vercel Analytics
- Use CDN for static assets
- Implement lazy loading

### 2. Backend
- Enable Supabase caching
- Use connection pooling
- Monitor API response times

### 3. Database
- Optimize queries
- Add indexes where needed
- Monitor storage usage
