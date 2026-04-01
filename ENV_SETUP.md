# Environment Variables Setup Guide

## Quick Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your actual values in `.env`:**
   - Get Supabase keys from your Supabase dashboard
   - Add your Xendit API keys
   - Set a secure JWT secret key

3. **Never commit `.env` to Git!**
   - It's already in `.gitignore`
   - Only `.env.example` should be in version control

## Required Environment Variables

### Supabase (Required)
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
DATABASE_URL=postgresql://postgres:your_password@db.your-project.supabase.co:5432/postgres
```

### JWT Security (Required)
```env
JWT_SECRET_KEY=generate-a-secure-random-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Xendit Payments (Required for donations)
```env
XENDIT_SECRET_KEY=your_xendit_secret_key
XENDIT_PUBLIC_KEY=your_xendit_public_key
XENDIT_WEBHOOK_TOKEN=your_webhook_token
XENDIT_DONATION_LINK=https://checkout-staging.xendit.co/donation/Maker
XENDIT_LINK_EXPIRY_DAYS=30
```

## Optional Environment Variables

### AI Features
```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo
```

### Email Notifications
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Monitoring
```env
SENTRY_DSN=your_sentry_dsn
```

### Caching (Redis)
```env
REDIS_URL=redis://localhost:6379
```

## Subscription Tiers

### Free Tier (Default)
- **5 projects** per account
- 100 AI actions per month
- 100MB storage
- 10 deployments per month
- 5 database tables

### Premium Tier
- **50 projects** per account
- Unlimited AI actions
- Unlimited storage
- Unlimited deployments
- Unlimited database tables
- Priority support

## Security Notes

1. **Never expose secrets in frontend code**
2. **Use environment variables for all sensitive data**
3. **Rotate keys regularly**
4. **Use HTTPS in production**
5. **Validate all environment variables on startup**

## Deployment Environment Variables

### Vercel (Frontend)
Set these in Vercel dashboard:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_XENDIT_PUBLIC_KEY`

### Supabase (Backend)
Set these in Supabase dashboard:
- `JWT_SECRET`
- `SERVICE_ROLE_KEY`
- `DATABASE_URL`

## Xendit Link Monitoring

The system automatically monitors your Xendit donation link expiry:
- **Warning**: 5 days before expiry
- **Critical**: When expired
- **Console notifications**: Displayed on every server start

To update your donation link:
1. Generate new link in Xendit dashboard
2. Update `XENDIT_DONATION_LINK` in your `.env`
3. Restart the application

## Development vs Production

### Development
```env
DEBUG=true
DATABASE_URL=postgresql://postgres:password@localhost:5432/xenitide_dev
```

### Production
```env
DEBUG=false
DATABASE_URL=postgresql://postgres:secure_password@db.supabase.co:5432/postgres
```
