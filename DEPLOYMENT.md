# Tillie Backend - Render Deployment Guide

## Pre-Deployment Checklist ✅

### 1. Environment Variables Setup
- [x] SECRET_KEY configured with environment variable
- [x] DEBUG set to False for production
- [x] ALLOWED_HOSTS configured for Render domains
- [x] Database URL configured for PostgreSQL
- [x] Redis URL configured for caching

### 2. Dependencies & Configuration
- [x] CORS headers configured for frontend communication
- [x] WhiteNoise configured for static file serving
- [x] Gunicorn configured as WSGI server
- [x] PostgreSQL adapter (psycopg2-binary) included
- [x] Security settings enabled for production

### 3. Static Files & Database
- [x] Static files collection configured
- [x] Database migrations ready
- [x] Build script created for automated deployment

## Deployment Steps

### Step 1: Prepare Your Repository
1. Commit all changes to your main branch
2. Push to GitHub: `git push origin main`

### Step 2: Create Render Web Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `tillie-backend` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn tillie_backend.wsgi:application`
   - **Plan**: `Free` (for free tier)

### Step 3: Set Environment Variables
In your Render service settings, add these environment variables:

```bash
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,tillie-backend.onrender.com
```

**To generate a new SECRET_KEY:**
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Step 4: Database Setup
Render will automatically:
- Create a PostgreSQL database
- Set the `DATABASE_URL` environment variable
- Handle database connections

### Step 5: Redis Setup (Optional)
For rate limiting functionality:
1. Add Redis add-on in Render (paid feature)
2. Or disable rate limiting by setting `RATELIMIT_ENABLE=False`

### Step 6: Deploy
1. Click "Create Web Service"
2. Render will automatically:
   - Install dependencies from `requirements.txt`
   - Run `collectstatic` for static files
   - Run database migrations
   - Start your Django application

## Post-Deployment

### Verify Deployment
1. Check your app URL: `https://your-app-name.onrender.com`
2. Test API endpoints:
   - `GET /admin/` - Django admin
   - `POST /api/auth/register/` - User registration
   - `POST /api/auth/login/` - User login

### Create Superuser
Connect to your Render service shell and create an admin user:
```bash
python manage.py createsuperuser
```

### Update Frontend CORS
Add your frontend URL to `CORS_ALLOWED_ORIGINS` in settings:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend-app.netlify.app",  # Add your frontend URL
]
```

## Troubleshooting

### Common Issues
1. **Static files not loading**: Ensure `collectstatic` runs in build script
2. **Database errors**: Check `DATABASE_URL` environment variable
3. **CORS errors**: Verify frontend URL in `CORS_ALLOWED_ORIGINS`
4. **Secret key errors**: Generate and set a proper `SECRET_KEY`

### Logs
View deployment logs in Render dashboard:
- Build logs: Check for dependency installation issues
- Runtime logs: Check for application errors

### Environment Variables Check
Ensure all required variables are set:
- `SECRET_KEY` ✅
- `DEBUG=False` ✅
- `ALLOWED_HOSTS` ✅
- `DATABASE_URL` (auto-set by Render) ✅

## API Endpoints
Your deployed backend will have these endpoints:
- `/admin/` - Django admin interface
- `/api/auth/` - Authentication endpoints
- `/api/shops/` - Shop management
- `/api/inventory/` - Inventory management
- `/api/orders/` - Order management

## Security Notes
- Never commit `.env` files with real secrets
- Use strong, unique SECRET_KEY for production
- Keep DEBUG=False in production
- Regularly update dependencies for security patches
