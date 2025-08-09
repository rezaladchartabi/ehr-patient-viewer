# EHR System Deployment Guide

This guide will help you deploy your EHR system so your colleagues can access it online.

## 🚀 Quick Deployment Options

### Option 1: Render (Recommended - Free & Easy)

**Step 1: Prepare Your Code**
1. Create a GitHub repository and push your code
2. Make sure your database file is included

**Step 2: Deploy on Render**
1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `ehr-system`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

**Step 3: Deploy Frontend**
1. Create another web service for the React app
2. Configure:
   - **Name**: `ehr-frontend`
   - **Environment**: `Static Site`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`
   - **Environment Variable**: `REACT_APP_API_URL=https://your-backend-url.onrender.com`

### Option 2: Railway (Alternative - Free Tier)

**Step 1: Deploy Backend**
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variable: `PORT=8000`
4. Deploy

**Step 2: Deploy Frontend**
1. Create a new service for the frontend
2. Set build command: `npm install && npm run build`
3. Set environment variable: `REACT_APP_API_URL=https://your-backend-url.railway.app`

### Option 3: Heroku (Paid but Reliable)

**Step 1: Install Heroku CLI**
```bash
# macOS
brew install heroku/brew/heroku

# Or download from heroku.com
```

**Step 2: Deploy Backend**
```bash
cd backend
heroku create your-ehr-backend
git add .
git commit -m "Deploy backend"
git push heroku main
```

**Step 3: Deploy Frontend**
```bash
cd ../
heroku create your-ehr-frontend
git add .
git commit -m "Deploy frontend"
git push heroku main
```

## 🔧 Manual Deployment Steps

### Step 1: Prepare Your Environment

1. **Copy Database File**
```bash
cp /Users/mohammadreza.ladchartabi/Downloads/condition_I82401_mimic_iv_data/ehr_data.sqlite3 ./backend/
```

2. **Update API URL in React App**
```bash
# Create .env file in ehr-ui directory
echo "REACT_APP_API_URL=https://your-backend-url.com" > .env
```

### Step 2: Deploy Backend

**Using Python Anywhere (Free)**
1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload your backend folder
3. Install requirements: `pip install -r requirements.txt`
4. Run: `python main.py`

**Using DigitalOcean App Platform**
1. Create account at [digitalocean.com](https://digitalocean.com)
2. Create new app from GitHub
3. Select Python environment
4. Set build command: `pip install -r requirements.txt`
5. Set run command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3: Deploy Frontend

**Using Netlify (Free)**
1. Go to [netlify.com](https://netlify.com)
2. Drag and drop your `build` folder
3. Set environment variable: `REACT_APP_API_URL=https://your-backend-url.com`

**Using Vercel (Free)**
1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Set environment variable: `REACT_APP_API_URL=https://your-backend-url.com`

## 🔒 Security Considerations

### For Production Use

1. **Add Authentication**
```python
# Add to main.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    # Add your authentication logic here
    pass
```

2. **Restrict CORS**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

3. **Use Environment Variables**
```python
import os
DB_PATH = os.getenv("DB_PATH", "ehr_data.sqlite3")
```

## 📱 Sharing with Colleagues

### Option 1: Public URL
- Share the frontend URL with your colleagues
- They can access it from any device with internet

### Option 2: Internal Network
- Deploy on your organization's internal server
- Share the internal IP address
- Example: `http://192.168.1.100:3000`

### Option 3: VPN Access
- Set up VPN for secure remote access
- Deploy on internal server
- Colleagues connect via VPN

## 🛠️ Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check that your backend CORS settings include your frontend domain
   - Ensure both services are running

2. **Database Not Found**
   - Verify the database file is in the correct location
   - Check file permissions

3. **Port Issues**
   - Make sure ports are not blocked by firewall
   - Use environment variables for port configuration

### Performance Optimization

1. **Database Indexing**
```sql
CREATE INDEX idx_patient_id ON condition(patient_id);
CREATE INDEX idx_patient_id ON medication(patient_id);
-- Add similar indexes for other tables
```

2. **API Caching**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

## 📞 Support

If you encounter issues:
1. Check the deployment platform's logs
2. Verify all environment variables are set
3. Test the API endpoints directly
4. Check browser console for frontend errors

## 🎯 Recommended Deployment Stack

**For Small Teams (Free):**
- Backend: Render or Railway
- Frontend: Netlify or Vercel
- Database: SQLite (included)

**For Larger Teams (Paid):**
- Backend: DigitalOcean App Platform
- Frontend: Vercel Pro
- Database: PostgreSQL on DigitalOcean
- Monitoring: Sentry for error tracking

