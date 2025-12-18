# Shopify AI Platform - Deployment Package

🚀 **Ready-to-deploy** minimal package for Shopify AI Platform with FastAPI backend + Streamlit frontend.

## 📦 What's Included

```
deployment/
├── backend/
│   ├── __init__.py
│   └── main_minimal.py          # FastAPI backend (3 endpoints)
├── ui/
│   ├── components/              # UI theme & components
│   └── shopify_platform.py      # Streamlit dashboard
├── .streamlit/
│   └── config.toml              # Streamlit theme
├── requirements-backend.txt      # Railway dependencies
├── requirements-frontend.txt     # Streamlit dependencies
├── Procfile                      # Railway start command
├── railway.json                  # Railway configuration
├── runtime.txt                   # Python 3.11.9
├── packages.txt                  # System dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🎯 Quick Start - Local Testing

### Prerequisites
- **Python 3.11** (Required! Python 3.13 has FastAPI compatibility issues)
- Git
- GitHub account

### 1️⃣ Test Backend Locally

```bash
# Install dependencies
pip install -r requirements-backend.txt

# Run backend server
python -m uvicorn backend.main_minimal:app --host 0.0.0.0 --port 8000 --reload
```

**Test endpoints:**
```powershell
# Root
Invoke-RestMethod -Uri "http://localhost:8000" -Method Get

# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get

# Ready check  
Invoke-RestMethod -Uri "http://localhost:8000/ready" -Method Get
```

### 2️⃣ Test Frontend Locally

```bash
# Install dependencies
pip install -r requirements-frontend.txt

# Run Streamlit
streamlit run ui/shopify_platform.py
```

Open: http://localhost:8501

## ☁️ Deploy to Cloud (Free!)

### Step 1: Deploy Backend to Railway

1. **Create Railway Account**: https://railway.app
   - Use GitHub Student Pack for extra credits
   - Free tier: $5 credit/month

2. **Create New Project**:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Python

3. **Configure Environment Variables**:
   Click "Variables" and add:
   ```
   GROQ_API_KEY=gsk_your_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   PORT=8000
   ```

4. **Get Groq API Key** (Free):
   - Visit: https://console.groq.com/keys
   - Sign up and create API key
   - Copy and paste into Railway variables

5. **Deploy**:
   - Railway auto-deploys using `Procfile`
   - Wait for build to complete (~2-3 minutes)
   - Copy your Railway URL: `https://your-app.railway.app`

### Step 2: Deploy Frontend to Streamlit Cloud

1. **Create Streamlit Account**: https://streamlit.io/cloud
   - Sign in with GitHub
   - 100% Free tier

2. **Create New App**:
   - Click "New app"
   - Select your repository
   - **Main file path**: `ui/shopify_platform.py`
   - **Python version**: 3.11

3. **Advanced Settings**:
   - Requirements file: `requirements-frontend.txt`
   - Add in **Secrets** (optional):
     ```toml
     BACKEND_URL = "https://your-railway-app.railway.app"
     ```

4. **Deploy**:
   - Click "Deploy!"
   - Wait for build (~3-5 minutes)
   - Your app will be at: `https://your-app.streamlit.app`

### Step 3: Update CORS (Important!)

After deploying to Streamlit, update your Railway backend:

1. Go to Railway dashboard → Your project → Variables
2. Add:
   ```
   ALLOWED_ORIGINS=https://your-app.streamlit.app,http://localhost:8501
   ```
3. Or edit `backend/main_minimal.py`:
   ```python
   allow_origins=["https://your-app.streamlit.app", "*"]
   ```

## 📋 Deployment Checklist

### Before Pushing to GitHub

- [ ] Review `.env.example` - don't commit your actual `.env`!
- [ ] Update `.gitignore` if needed
- [ ] Test backend locally (all 3 endpoints work)
- [ ] Test frontend locally (UI displays correctly)
- [ ] Verify `runtime.txt` has Python 3.11.9
- [ ] Verify `Procfile` points to correct app

### Railway Deployment

- [ ] Create Railway project
- [ ] Connect GitHub repository
- [ ] Add `GROQ_API_KEY` to variables
- [ ] Wait for successful build
- [ ] Test health endpoint: `https://your-app.railway.app/health`
- [ ] Copy Railway URL

### Streamlit Deployment

- [ ] Create Streamlit Cloud account
- [ ] Deploy from GitHub
- [ ] Set main file: `ui/shopify_platform.py`
- [ ] Set Python version: 3.11
- [ ] Wait for successful build
- [ ] Update Railway CORS with Streamlit URL

## 🐛 Troubleshooting

### Railway Issues

**Build fails with package errors:**
- Check `requirements-backend.txt` versions
- View logs in Railway dashboard
- Ensure Python 3.11 is used

**Health check fails:**
```bash
# Test locally first
curl http://localhost:8000/health
```

**500 Internal Server Error:**
- Check Railway logs for errors
- Verify environment variables are set
- Ensure no `Dockerfile` in folder (uses Procfile)

### Streamlit Issues

**Import errors:**
- Verify `components` folder is included
- Check `requirements-frontend.txt` is complete

**Can't connect to backend:**
- Test backend URL directly in browser
- Check CORS configuration
- Verify `BACKEND_URL` in Streamlit secrets

### Python Version Issues

**FastAPI middleware error:**
```
ValueError: too many values to unpack (expected 2)
```
- **Cause**: Using Python 3.13
- **Fix**: Use Python 3.11 (specified in `runtime.txt`)

## 📚 API Endpoints

### Current (Minimal Backend)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |

### Full Backend Features (Optional)

To enable full AI features, replace `backend/main_minimal.py` with the full backend from parent folder:

- Customer support AI
- Content generation
- Data scraping
- Form filling automation
- SEO optimization
- Multi-tenant database

## 🔐 Security Notes

**For Production:**

1. **Never commit `.env`** - It's in `.gitignore`
2. **Update CORS** - Replace `"*"` with actual Streamlit URL
3. **Rotate API keys** - Regenerate Groq key periodically
4. **Use secrets managers** - Railway Variables, Streamlit Secrets
5. **Enable HTTPS** - Both platforms provide it automatically

## 📈 Monitoring

**Railway:**
- Built-in metrics dashboard
- Real-time logs
- Resource usage tracking

**Streamlit:**
- App analytics
- Usage statistics
- Error tracking

## 💰 Cost Estimate

- **Railway**: $5 free credits/month (enough for testing)
- **Streamlit Cloud**: 100% free (unlimited)
- **Groq API**: Free tier (generous limits)

**Total monthly cost**: $0 (free tiers sufficient for development)

## 🔗 Useful Links

- [Groq Console](https://console.groq.com/keys) - Get API keys
- [Railway Docs](https://docs.railway.app) - Deployment guide
- [Streamlit Docs](https://docs.streamlit.io/streamlit-community-cloud) - Cloud deployment
- [GitHub Student Pack](https://education.github.com/pack) - Free credits

## 📞 Support

Issues? Check troubleshooting section or:
- Railway: https://help.railway.app
- Streamlit: https://discuss.streamlit.io
- Groq: https://console.groq.com/docs

---

**Ready to deploy?** Push this folder to GitHub and follow the steps above! 🚀
