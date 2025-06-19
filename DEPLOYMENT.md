# 🚀 Deployment Guide

This guide covers deploying the HTS Oracle application with backend on Heroku and frontend on Netlify.

## 📋 Prerequisites

- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
- [Git](https://git-scm.com/) installed
- [Netlify account](https://netlify.com)
- [Heroku account](https://heroku.com)
- API keys for:
  - Anthropic (Claude AI)
  - Pinecone (Vector Database)

## 🔧 Backend Deployment (Heroku)

### 1. Create Heroku App

```bash
# Login to Heroku
heroku login

# Create new app (replace with your preferred name)
heroku create hts-oracle-backend

# Add Python buildpack
heroku buildpacks:set heroku/python -a hts-oracle-backend
```

### 2. Set Environment Variables

```bash
# Required API keys
heroku config:set ANTHROPIC_API_KEY="your_anthropic_api_key" -a hts-oracle-backend
heroku config:set PINECONE_API_KEY="your_pinecone_api_key" -a hts-oracle-backend

# Environment configuration
heroku config:set FLASK_ENV="production" -a hts-oracle-backend
heroku config:set NETLIFY_URL="https://hts-oracle.netlify.app" -a hts-oracle-backend
heroku config:set FRONTEND_URL="https://hts-oracle.netlify.app" -a hts-oracle-backend

# Pinecone configuration
heroku config:set PINECONE_INDEX_NAME="commodity-hts-codes-new" -a hts-oracle-backend
heroku config:set PINECONE_DIMENSION="1024" -a hts-oracle-backend
```

### 3. Deploy Backend

```bash
# From the project root directory
cd backend

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial backend commit"

# Add Heroku remote
heroku git:remote -a hts-oracle-backend

# Deploy
git push heroku main
```

### 4. Verify Backend Deployment

```bash
# Check logs
heroku logs --tail -a hts-oracle-backend

# Test health endpoint
curl https://hts-oracle-backend.herokuapp.com/api/health
```

## 🎨 Frontend Deployment (Netlify)

### Option A: Git-based Deployment (Recommended)

1. **Push to GitHub/GitLab**
   ```bash
   # From project root
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Connect to Netlify**
   - Go to [Netlify Dashboard](https://app.netlify.com)
   - Click "New site from Git"
   - Connect your repository
   - Set build settings:
     - **Base directory**: `frontend`
     - **Build command**: `npm run build`
     - **Publish directory**: `frontend/dist`

3. **Configure Environment Variables**
   - In Netlify site settings → Environment variables:
   ```
   VITE_API_URL = https://hts-oracle-backend.herokuapp.com
   ```

4. **Custom Domain (Optional)**
   - In Netlify site settings → Domain management
   - Add custom domain: `hts-oracle.netlify.app`

### Option B: Manual Deployment

```bash
# From frontend directory
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Deploy
netlify deploy --prod --dir=dist
```

## 🔍 Post-Deployment Verification

### 1. Backend Health Check
```bash
curl https://hts-oracle-backend.herokuapp.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "api_ready": true,
  "version": "1.0.0",
  "environment": "production"
}
```

### 2. Frontend Functionality Test
- Visit your Netlify URL
- Test a product classification
- Verify PDF export works
- Check console for any errors

### 3. CORS Verification
- Open browser developer tools
- Submit a classification request
- Ensure no CORS errors in console

## 🛠️ Troubleshooting

### Common Backend Issues

**App won't start**
```bash
heroku logs --tail -a hts-oracle-backend
```
- Check for missing environment variables
- Verify Python version in `runtime.txt`
- Check `requirements.txt` dependencies

**CORS errors**
- Verify `NETLIFY_URL` environment variable
- Check allowed origins in `app.py`

**API key issues**
- Verify environment variables are set correctly
- Check API key validity

### Common Frontend Issues

**Build failures**
- Check Node.js version (should be 18+)
- Verify all dependencies in `package.json`
- Check for TypeScript errors

**API connection issues**
- Verify `VITE_API_URL` environment variable
- Check network tab in browser developer tools
- Ensure backend is running

## 📊 Monitoring

### Heroku Monitoring
```bash
# View logs
heroku logs --tail -a hts-oracle-backend

# Check dyno status
heroku ps -a hts-oracle-backend

# View metrics
heroku addons:open papertrail -a hts-oracle-backend
```

### Netlify Monitoring
- Check build logs in Netlify dashboard
- Monitor function logs (if using Netlify functions)
- Review analytics in Netlify dashboard

## 🔄 Updates and Maintenance

### Backend Updates
```bash
# From backend directory
git add .
git commit -m "Update backend"
git push heroku main
```

### Frontend Updates
- Push to your Git repository
- Netlify will automatically rebuild and deploy

### Environment Variable Updates
```bash
# Heroku
heroku config:set VARIABLE_NAME="new_value" -a hts-oracle-backend

# Netlify
# Update via dashboard → Site settings → Environment variables
```

## 📈 Scaling

### Backend Scaling (Heroku)
```bash
# Scale up dynos
heroku ps:scale web=2 -a hts-oracle-backend

# Upgrade dyno type
heroku ps:type Standard-1X -a hts-oracle-backend
```

### Frontend Scaling (Netlify)
- Netlify automatically handles CDN distribution
- No manual scaling required for static sites

## 💰 Cost Optimization

### Heroku Free Tier
- Use Eco dynos ($5/month) for production
- Consider scaling down during off-hours

### Netlify Free Tier
- 100GB bandwidth per month
- 300 build minutes per month
- Perfect for most use cases

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit API keys to Git
   - Use different keys for development/production
   - Rotate keys regularly

2. **CORS Configuration**
   - Only allow necessary origins
   - Use HTTPS in production
   - Review periodically

3. **Dependencies**
   - Keep dependencies updated
   - Use `npm audit` to check for vulnerabilities
   - Monitor security advisories

## 📞 Support

If you encounter issues:

1. Check the logs first
2. Verify environment variables
3. Test API endpoints directly
4. Review this deployment guide
5. Check official documentation:
   - [Heroku Python Documentation](https://devcenter.heroku.com/categories/python-support)
   - [Netlify Documentation](https://docs.netlify.com/)

---

**Deployment URLs:**
- **Backend**: https://hts-oracle-backend.herokuapp.com
- **Frontend**: https://hts-oracle.netlify.app