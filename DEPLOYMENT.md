# 🚀 Deployment Guide

This guide covers deploying the HTS Oracle application with a Flask backend on Render and a Vite frontend on Netlify.

## 📋 Prerequisites

- [Git](https://git-scm.com/)
- [Render account](https://render.com/)
- [Netlify account](https://netlify.com)
- API keys for:
  - OpenAI (embeddings)
  - Pinecone (vector database)
  - Anthropic (Claude)

## 🔧 Backend Deployment (Render)

### 1. Create a Render Web Service

1. Go to the Render dashboard → **New** → **Web Service**
2. Connect your Git repository
3. Configure service settings:
   - **Root Directory**: `backend`
   - **Runtime**: Python
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --preload
     ```

### 2. Set Environment Variables

Add the following in Render → Service → **Environment**:

```
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

FLASK_ENV=production
NETLIFY_URL=https://your-netlify-site.netlify.app
FRONTEND_URL=https://your-netlify-site.netlify.app

# Optional extra origins (comma-separated)
# Example: CORS_ORIGINS=https://htshelper.netlify.app,https://admin.yourdomain.com
CORS_ORIGINS=

# Optional
PINECONE_INDEX_NAME=hts-codes
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

### 3. Deploy

- Render deploys automatically on push to your repository.
- You can also trigger a manual deploy from the Render dashboard.

### 4. Verify Backend Deployment

```
curl https://your-render-service.onrender.com/api/health
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
   VITE_API_URL = https://hts-classifier-pemj.onrender.com
   ```

4. **Custom Domain (Optional)**
   - In Netlify site settings → Domain management
   - Add your custom domain

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
curl https://your-render-service.onrender.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production"
}
```

### 2. Frontend Functionality Test
- Visit your Netlify URL
- Submit a product description
- Verify clarifying questions appear when needed
- Open result cards and check USITC links

### 3. CORS Verification
- Open browser developer tools
- Submit a classification request
- Ensure no CORS errors in console

## 🛠️ Troubleshooting

### Common Backend Issues

**App won't start**
- Check Render → Logs
- Verify environment variables are set
- Check `requirements.txt` dependencies

**CORS errors**
- Verify `NETLIFY_URL` / `FRONTEND_URL` environment variables
- Check allowed origins in `app.py`

**API key issues**
- Verify environment variables are set correctly
- Check API key validity

### Common Frontend Issues

**Build failures**
- Check Node.js version (should be 18+)
- Verify all dependencies in `package.json`
- Check for ESLint errors

**API connection issues**
- Verify `VITE_API_URL` environment variable
- Check network tab in browser developer tools
- Ensure backend is running

## 📊 Monitoring

### Render Monitoring
- View logs in the Render dashboard
- Check deploy history and health checks

### Netlify Monitoring
- Check build logs in Netlify dashboard
- Review analytics in Netlify dashboard

## 🔄 Updates and Maintenance

### Backend Updates (Render)
- Push to your Git repository
- Render will automatically rebuild and deploy

### Frontend Updates (Netlify)
- Push to your Git repository
- Netlify will automatically rebuild and deploy

### Environment Variable Updates
- Update Render and Netlify environment variables via their dashboards

## 📈 Scaling

### Backend Scaling (Render)
- Scale service plan or instance size in Render dashboard

### Frontend Scaling (Netlify)
- Netlify automatically handles CDN distribution
- No manual scaling required for static sites

## 💰 Cost Optimization

### Render
- Free tier services may sleep on inactivity
- Consider paid plans for always-on usage

### Netlify
- 100GB bandwidth per month on free tier
- 300 build minutes per month

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit API keys to Git
   - Use different keys for development/production
   - Rotate keys regularly

2. **CORS Configuration**
   - Only allow necessary origins
   - Use HTTPS in production

3. **Dependencies**
   - Keep dependencies updated
   - Monitor security advisories

## 📞 Support

If you encounter issues:

1. Check the logs first
2. Verify environment variables
3. Test API endpoints directly
4. Review this deployment guide
5. Check official documentation:
   - [Render Docs](https://render.com/docs)
   - [Netlify Documentation](https://docs.netlify.com/)

---

**Deployment URLs (example):**
- **Backend**: https://hts-oracle-backend.onrender.com
- **Frontend**: https://hts-oracle.netlify.app
