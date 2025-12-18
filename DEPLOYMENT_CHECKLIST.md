# 🚀 DEPLOYMENT CHECKLIST

## ✅ Pre-Deployment (Local Testing)

### Backend Testing
- [x] Backend runs successfully with Python 3.11
- [x] All 3 endpoints working (`/`, `/health`, `/ready`)
- [x] CORS middleware configured
- [x] Environment variables template created (`.env.example`)
- [x] `.gitignore` configured

### Frontend Testing  
- [x] Streamlit runs without errors
- [x] UI components display correctly (icons, colors, theme)
- [x] `components` folder included

### Files Ready
- [x] `requirements-backend.txt` (17 packages)
- [x] `requirements-frontend.txt` (8 packages)
- [x] `Procfile` (Railway start command)
- [x] `railway.json` (Railway config)
- [x] `runtime.txt` (Python 3.11.9)
- [x] `packages.txt` (libpq-dev)
- [x] `README.md` (deployment guide)
- [x] `.gitignore` (excludes .env, __pycache__, etc.)
- [x] `.env.example` (environment template)

## 📦 Push to GitHub

```bash
# Initialize git (if not already)
cd deployment
git init

# Add all files
git add .

# Commit
git commit -m "Initial deployment package - Shopify AI Platform"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

## ☁️ Railway Deployment

### Step 1: Create Project
- [ ] Go to https://railway.app
- [ ] Click "New Project"
- [ ] Select "Deploy from GitHub repo"
- [ ] Choose your deployment repository

### Step 2: Configure Variables
Add these in Railway Dashboard → Variables:
- [ ] `GROQ_API_KEY` = Get from https://console.groq.com/keys
- [ ] `GROQ_MODEL` = `llama-3.3-70b-versatile`
- [ ] `PORT` = `8000`

### Step 3: Verify Deployment
- [ ] Build completes successfully (~2-3 minutes)
- [ ] Health check passes
- [ ] Test endpoint: `https://your-app.railway.app/health`
- [ ] Copy Railway URL for Streamlit

## 🎨 Streamlit Cloud Deployment

### Step 1: Create App
- [ ] Go to https://streamlit.io/cloud
- [ ] Click "New app"
- [ ] Connect GitHub repository
- [ ] Main file: `ui/shopify_platform.py`
- [ ] Python version: `3.11`
- [ ] Requirements: `requirements-frontend.txt`

### Step 2: Configure (Optional)
Add in Secrets:
```toml
BACKEND_URL = "https://your-railway-app.railway.app"
```

### Step 3: Verify
- [ ] Build completes (~3-5 minutes)
- [ ] App loads without errors
- [ ] UI displays correctly
- [ ] Copy Streamlit URL

## 🔧 Post-Deployment

### Update CORS
Go to Railway → Variables → Add:
- [ ] `ALLOWED_ORIGINS` = `https://your-app.streamlit.app,http://localhost:8501`

Or update `backend/main_minimal.py` and push:
```python
allow_origins=["https://your-app.streamlit.app"]
```

### Test Integration
- [ ] Open Streamlit app
- [ ] Verify no CORS errors in console
- [ ] Test backend connectivity

## 🐛 Troubleshooting Completed

If issues occur:

### Railway
- [ ] Check logs: Railway Dashboard → Deployments → View logs
- [ ] Verify Python 3.11 is being used
- [ ] Ensure no `Dockerfile` exists
- [ ] Test health endpoint directly

### Streamlit
- [ ] Check app logs in Streamlit dashboard
- [ ] Verify `components` folder is included
- [ ] Test with Python 3.11 locally first

## 🎉 Success Criteria

Your deployment is successful when:
- ✅ Railway backend responds to `/health` with 200 OK
- ✅ Streamlit app loads without import errors
- ✅ UI displays with correct theme and icons
- ✅ No CORS errors in browser console

## 📊 Monitoring

### Railway
- Check metrics: Dashboard → Metrics
- View logs: Dashboard → Deployments
- Resource usage: Dashboard → Usage

### Streamlit
- App analytics: Streamlit dashboard
- Error tracking: App logs
- Usage stats: Analytics tab

---

**Current Status:** ✅ Ready to push to GitHub and deploy!

**Estimated Deployment Time:**
- Railway: 2-3 minutes
- Streamlit: 3-5 minutes
- Total: ~10 minutes

**Cost:** $0 (Free tiers sufficient for development)
