# 🚀 Render Deployment Guide for EHR System

This guide will walk you through deploying your EHR system on Render in under 10 minutes.

## 📋 Prerequisites

- GitHub account
- Render account (free)
- Your code committed to GitHub

## 🎯 Step-by-Step Deployment

### Step 1: Create GitHub Repository

1. **Go to GitHub.com** and sign in
2. **Click "New repository"**
3. **Name it**: `ehr-system` or `ehr-patient-viewer`
4. **Make it Public** (for free Render deployment)
5. **Don't initialize** with README (we already have one)
6. **Click "Create repository"**

### Step 2: Push Your Code to GitHub

Run these commands in your terminal:

```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/ehr-system.git

# Push your code
git push -u origin main
```

### Step 3: Deploy on Render

1. **Go to [render.com](https://render.com)**
2. **Sign up** with your GitHub account
3. **Click "New +"** → **"Blueprint"**
4. **Connect your GitHub repository**
5. **Select your repository** (`ehr-system`)
6. **Click "Connect"**

### Step 4: Configure Services

Render will automatically detect the `render.yaml` file and create two services:

#### Backend Service (ehr-backend)
- **Type**: Web Service
- **Environment**: Python
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Plan**: Free

#### Frontend Service (ehr-frontend)
- **Type**: Static Site
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `build`
- **Plan**: Free

### Step 5: Deploy

1. **Click "Create Blueprint"**
2. **Wait for deployment** (5-10 minutes)
3. **Both services will deploy automatically**

## 🔧 Manual Configuration (if needed)

If the automatic deployment doesn't work, create services manually:

### Backend Service
1. **Click "New +"** → **"Web Service"**
2. **Connect your repository**
3. **Configure**:
   - **Name**: `ehr-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

### Frontend Service
1. **Click "New +"** → **"Static Site"**
2. **Connect your repository**
3. **Configure**:
   - **Name**: `ehr-frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`
   - **Environment Variable**: `REACT_APP_API_URL=https://your-backend-url.onrender.com`

## 🌐 Access Your Application

After deployment, you'll get two URLs:

- **Backend API**: `https://ehr-backend-xxxxx.onrender.com`
- **Frontend App**: `https://ehr-frontend-xxxxx.onrender.com`

## 🔄 Updating Your Application

To update your application:

1. **Make changes** to your code
2. **Commit and push** to GitHub:
   ```bash
   git add .
   git commit -m "Update EHR system"
   git push
   ```
3. **Render will automatically redeploy** your services

## 🛠️ Troubleshooting

### Common Issues

1. **Build Fails**
   - Check the build logs in Render dashboard
   - Verify all dependencies are in `requirements.txt`
   - Ensure database file is included

2. **Frontend Can't Connect to Backend**
   - Verify `REACT_APP_API_URL` environment variable is set
   - Check CORS settings in backend
   - Test backend API directly

3. **Database Not Found**
   - Ensure `ehr_data.sqlite3` is in the `backend/` directory
   - Check file permissions

### Performance Tips

1. **Enable Auto-Deploy** (on by default)
2. **Use Environment Variables** for configuration
3. **Monitor logs** for any issues
4. **Set up alerts** for service downtime

## 📱 Sharing with Colleagues

Once deployed:

1. **Share the frontend URL** with your colleagues
2. **They can access it** from any device with internet
3. **No installation required** - just a web browser

## 🔒 Security Notes

For production use:
- **Add authentication** to your API
- **Restrict CORS** to your domain
- **Use environment variables** for sensitive data
- **Consider upgrading** to a paid plan for better performance

## 🎉 Success!

Your EHR system is now live and accessible to your colleagues!

**Frontend URL**: `https://ehr-frontend-xxxxx.onrender.com`
**Backend API**: `https://ehr-backend-xxxxx.onrender.com`

Share the frontend URL with your team and start using your EHR system!
