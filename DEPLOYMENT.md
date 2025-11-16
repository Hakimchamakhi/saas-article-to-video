# Free Deployment Guide: Vercel + Render

This guide will walk you through deploying your Blog-to-Video Converter application for **FREE** using:
- **Vercel** for the React frontend
- **Render** for the FastAPI backend, Celery worker, and Redis

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Deploy Backend on Render](#deploy-backend-on-render)
3. [Deploy Frontend on Vercel](#deploy-frontend-on-vercel)
4. [Configure Environment Variables](#configure-environment-variables)
5. [Testing Your Deployment](#testing-your-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

1. **GitHub Account** - Your code should be pushed to a GitHub repository
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com) (free)
3. **Render Account** - Sign up at [render.com](https://render.com) (free)
4. **API Keys**:
   - OpenAI API Key from [platform.openai.com](https://platform.openai.com/api-keys)
   - Pexels API Key from [pexels.com/api](https://www.pexels.com/api/)

---

## Deploy Backend on Render

Render will host your FastAPI backend, Celery worker, and Redis database for free.

### Step 1: Create a New Blueprint

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file

### Step 2: Configure the Blueprint

The `render.yaml` file defines three services:
- **Web Service** (FastAPI backend)
- **Worker** (Celery worker for video processing)
- **Redis** (Message broker)

Review the configuration and click **"Apply"**

### Step 3: Set Environment Variables

After the services are created, you need to add your API keys:

1. Go to your **blog-to-video-api** web service dashboard
2. Navigate to **"Environment"** tab
3. Add the following environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PEXELS_API_KEY=your_pexels_api_key_here
   ```

4. Go to your **blog-to-video-worker** service dashboard
5. Navigate to **"Environment"** tab
6. Add the same environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PEXELS_API_KEY=your_pexels_api_key_here
   ```

### Step 4: Note Your Backend URL

After deployment completes (takes 5-10 minutes), you'll get a URL like:
```
https://blog-to-video-api.onrender.com
```

**IMPORTANT**: Save this URL - you'll need it for the frontend deployment!

### Step 5: Install FFmpeg on Render

Render's default environment doesn't include FFmpeg (required for video processing). You need to add a build command:

1. Go to your **blog-to-video-api** service
2. Navigate to **"Settings"** tab
3. Find **"Build Command"**
4. Update it to:
   ```bash
   apt-get update && apt-get install -y ffmpeg && pip install -r backend/requirements.txt
   ```

5. Do the same for the **blog-to-video-worker** service

6. Click **"Save Changes"** and redeploy both services

---

## Deploy Frontend on Vercel

Vercel will host your React frontend for free with automatic HTTPS and CDN.

### Step 1: Import Your Project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Vercel will auto-detect it's a Vite project

### Step 2: Configure Build Settings

1. **Framework Preset**: Vite (auto-detected)
2. **Root Directory**: `frontend`
3. **Build Command**: `npm run build`
4. **Output Directory**: `dist`

### Step 3: Add Environment Variable

Before deploying, add your backend API URL:

1. In the **"Environment Variables"** section, add:
   ```
   Name:  VITE_API_URL
   Value: https://blog-to-video-api.onrender.com/api
   ```
   (Replace with your actual Render backend URL from Step 4 above)

2. Make sure it's set for **Production**, **Preview**, and **Development**

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait 2-3 minutes for the build to complete
3. You'll get a URL like: `https://your-app.vercel.app`

### Step 5: Update CORS Settings (Important!)

Now that you have your frontend URL, you need to update the backend CORS settings:

1. Go to your Render dashboard
2. Open your **blog-to-video-api** service
3. Navigate to **"Environment"** tab
4. Add a new environment variable:
   ```
   FRONTEND_URL=https://your-app.vercel.app
   ```

5. Update the backend code to use this variable (see below)

**Update backend/main.py:**

Currently the backend has:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    ...
)
```

You should update it to:
```python
import os

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],  # Secure CORS for production
    ...
)
```

6. Commit and push this change to trigger a redeploy on Render

---

## Configure Environment Variables

### Backend Environment Variables (Render)

Set these in **both** the API and Worker services:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `PEXELS_API_KEY` | Your Pexels API key | `abc123...` |
| `REDIS_URL` | Auto-configured by Render | *(auto)* |
| `FRONTEND_URL` | Your Vercel frontend URL | `https://your-app.vercel.app` |

### Frontend Environment Variables (Vercel)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Your Render backend API URL | `https://blog-to-video-api.onrender.com/api` |

---

## Testing Your Deployment

### 1. Check Backend Health

Visit your backend URL in a browser:
```
https://blog-to-video-api.onrender.com/
```

You should see:
```json
{
  "message": "Blog to Video Converter API",
  "status": "running"
}
```

### 2. Check Services Status on Render

1. Go to Render dashboard
2. Verify all three services are **"Live"** (green):
   - blog-to-video-api (Web Service)
   - blog-to-video-worker (Worker)
   - blog-to-video-redis (Redis)

### 3. Test the Frontend

1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Paste a blog article URL
3. Click "Generate Video"
4. Wait for processing (2-5 minutes)
5. Download and watch your video!

### 4. Monitor Logs

**Backend Logs (Render):**
- Go to your web service → "Logs" tab
- Watch for API requests and errors

**Worker Logs (Render):**
- Go to your worker service → "Logs" tab
- Watch the video generation process

**Frontend Logs (Vercel):**
- Go to your Vercel project → "Deployments" → Click latest deployment → "Logs"

---

## Troubleshooting

### Issue: Backend shows "Application failed to respond"

**Solution:**
- Check that the PORT environment variable is being used correctly
- Verify FFmpeg is installed (check build logs)
- Check that all Python dependencies installed successfully

### Issue: Frontend can't connect to backend (CORS error)

**Solution:**
- Verify `VITE_API_URL` is set correctly in Vercel
- Check `FRONTEND_URL` is set in Render
- Update CORS settings in backend/main.py to allow your frontend domain

### Issue: Video generation fails

**Solution:**
- Check OpenAI API key is valid and has credits
- Check Pexels API key is valid
- Review Celery worker logs for specific errors
- Verify FFmpeg is installed on the worker service

### Issue: Redis connection errors

**Solution:**
- Ensure Redis service is running on Render
- Check that `REDIS_URL` is automatically connected in render.yaml
- Verify both API and Worker services have access to Redis

### Issue: "Cold start" delays on Render

**Note:** Render's free tier spins down services after 15 minutes of inactivity. The first request after inactivity will take 30-60 seconds to wake up.

**Solutions:**
- Upgrade to a paid plan for always-on services
- Use a service like [cron-job.org](https://cron-job.org) to ping your API every 10 minutes
- Accept the delay as a tradeoff for free hosting

### Issue: FFmpeg not found

**Solution:**
Update your build command on both API and Worker services:
```bash
apt-get update && apt-get install -y ffmpeg && pip install -r backend/requirements.txt
```

---

## Cost Breakdown

### Free Tier Limits

**Vercel Free Tier:**
- 100 GB bandwidth/month
- Unlimited deployments
- Automatic HTTPS
- Global CDN
- **Perfect for this frontend!**

**Render Free Tier:**
- 750 hours/month (enough for always-on services)
- 512 MB RAM per service
- Services spin down after 15 min inactivity
- 100 GB bandwidth/month
- **Good for testing, may need upgrade for heavy use**

### When to Upgrade

Consider upgrading to paid tiers when:
- You need faster video processing (more RAM/CPU)
- You want to eliminate cold start delays
- You exceed free tier bandwidth limits
- You need always-on services

**Estimated paid costs:**
- Render: $7-25/month (depending on service tier)
- Vercel: Usually stays free for personal projects

---

## Production Optimization Tips

### 1. Enable Caching
Add caching headers to serve generated videos faster

### 2. Use Object Storage
Instead of storing videos on Render's filesystem, use:
- AWS S3 (free tier: 5 GB)
- Cloudflare R2 (free: 10 GB)
- Backblaze B2 (free: 10 GB)

### 3. Add Video Cleanup
Automatically delete old videos to save space:
```python
# Add a cleanup job in worker.py
@celery_app.task
def cleanup_old_videos():
    # Delete videos older than 24 hours
    pass
```

### 4. Implement Rate Limiting
Prevent abuse by limiting requests per IP:
```python
# In backend/main.py
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/generate-video")
@limiter.limit("5/hour")
async def generate_video():
    ...
```

### 5. Monitor API Usage
- Set up billing alerts in OpenAI dashboard
- Monitor Pexels API usage
- Track video generation costs

---

## Alternative: Deploy Everything on Render

If you prefer to host both frontend and backend on Render:

1. Build the frontend into static files
2. Serve them from FastAPI using:
   ```python
   app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
   ```
3. Deploy as a single web service

**Pros:** Everything in one place, simpler configuration
**Cons:** Less optimized than Vercel for static sites

---

## Getting Help

If you encounter issues:

1. **Check Logs**: Always start with service logs on Render/Vercel
2. **API Status**: Verify your OpenAI and Pexels API keys are working
3. **Dependencies**: Ensure FFmpeg and all Python packages are installed
4. **Environment Variables**: Double-check all env vars are set correctly

---

## Next Steps

After successful deployment:

1. Add a custom domain (free on both Vercel and Render)
2. Set up monitoring and alerts
3. Implement video caching and cleanup
4. Add user authentication
5. Consider upgrading to paid tiers for better performance

Happy deploying! 🚀
