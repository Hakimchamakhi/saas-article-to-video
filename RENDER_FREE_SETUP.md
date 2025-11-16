# 🎉 100% FREE Render Deployment Guide

This guide shows you how to deploy your Blog-to-Video application on Render using **completely free services** - no payment information required!

## Architecture Overview

Your application will use these **FREE** services:
- ✅ **Render Web Service** (FastAPI backend) - FREE
- ✅ **Render Worker Service** (Celery background tasks) - FREE
- ✅ **Render Static Site** (React frontend) - FREE
- ✅ **External Redis** (Message broker) - FREE

## Prerequisites

You'll need:
1. GitHub account (to host your code)
2. Render account (free tier)
3. Free Redis instance (from Upstash or Railway)
4. Groq API key (100% FREE - no credit card!)
5. Pexels API key (100% FREE - for stock videos)

## Step 1: Get a FREE Redis Instance

You need Redis for Celery task queue. Choose **ONE** of these free options:

### Option A: Upstash Redis (Recommended - 10,000 requests/day free)

1. Go to https://upstash.com/
2. Sign up for free account
3. Click "Create Database"
4. Choose any region (closest to your Render region is best)
5. Click "Create"
6. Copy the **Redis URL** (looks like: `rediss://default:xxxxx@xxxxxx.upstash.io:6379`)

### Option B: Railway Redis (Free $5/month credit)

1. Go to https://railway.app/
2. Sign up for free account
3. Create new project
4. Click "+ New" → "Database" → "Add Redis"
5. Click on the Redis service
6. Go to "Connect" tab
7. Copy the **Redis URL** (looks like: `redis://default:xxxxx@xxxxx.railway.internal:6379`)

### Option C: Redis Cloud (30MB free)

1. Go to https://redis.com/try-free/
2. Sign up for free account
3. Create a new subscription (choose free tier)
4. Create a database
5. Copy the **Redis URL** from the configuration page

## Step 2: Get FREE API Keys

### Groq API Key (100% FREE - No Credit Card!)

1. Go to https://console.groq.com/
2. Sign up with your email or GitHub
3. Click on "API Keys" in the left sidebar
4. Click "Create API Key"
5. Copy your API key (starts with `gsk_...`)

**Why Groq?**
- Completely FREE (no credit card required)
- Fast inference with Llama models
- Generous rate limits for free tier
- No hidden costs

### Pexels API Key (100% FREE)

1. Go to https://www.pexels.com/api/
2. Click "Get Started"
3. Sign up for a free account
4. Go to your account settings
5. Generate an API key
6. Copy your API key

**Rate limits:** 200 requests/hour (more than enough!)

## Step 3: Push Your Code to GitHub

```bash
# If not already initialized
git init
git add .
git commit -m "Initial commit"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Step 4: Deploy to Render

### Option A: Using render.yaml (Automatic)

1. Go to https://render.com/
2. Sign in (no payment info needed!)
3. Click **"New +"** → **"Blueprint"**
4. Connect your GitHub repository
5. Select your repository
6. Render will detect `render.yaml` and show 3 services:
   - `blog-to-video-api` (Web Service)
   - `blog-to-video-worker` (Background Worker)
   - `blog-to-video-frontend` (Static Site)

### Option B: Manual Setup

If you prefer manual setup, create each service:

#### 1. Backend API (Web Service)
- Type: **Web Service**
- Environment: **Python**
- Build Command: `pip install -r backend/requirements.txt`
- Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- Plan: **Free**

#### 2. Celery Worker (Background Worker)
- Type: **Background Worker**
- Environment: **Python**
- Build Command: `pip install -r backend/requirements.txt`
- Start Command: `cd backend && celery -A worker.celery_app worker --loglevel=info`
- Plan: **Free**

#### 3. Frontend (Static Site)
- Type: **Static Site**
- Build Command: `cd frontend && npm install && npm run build`
- Publish Directory: `frontend/dist`
- Plan: **Free**

## Step 5: Configure Environment Variables

For **both** the backend API and worker services, add these environment variables:

### Required Variables:

1. **REDIS_URL**
   - Value: Your Redis URL from Step 1
   - Example: `rediss://default:xxxxx@xxxxxx.upstash.io:6379`

2. **GROQ_API_KEY** (100% FREE!)
   - Value: Your Groq API key from Step 2
   - Example: `gsk_xxxxxxxxxxxxxxxxx`
   - Get it from: https://console.groq.com/keys
   - No credit card required!

3. **PEXELS_API_KEY** (100% FREE!)
   - Value: Your Pexels API key from Step 2
   - Get it from: https://www.pexels.com/api/
   - Note: Free tier allows 200 requests/hour

### For the Frontend service:

1. **VITE_API_URL** (Set AFTER backend deploys!)
   - Value: Your backend API URL from Render (WITHOUT /api suffix)
   - Example: `https://blog-to-video-api.onrender.com`
   - **Important**: Wait for the backend service to deploy first, then copy its URL and add it here
   - After adding this, trigger a redeploy of the frontend service

## Step 6: Deploy!

1. Click **"Apply"** or **"Create"** to start the deployment
2. Wait for all services to build (first build takes 5-10 minutes)
3. All services will be on the **FREE tier** - no payment required! 🎉

## Step 7: Test Your Application

1. Once deployed, click on your frontend URL (e.g., `https://blog-to-video-frontend.onrender.com`)
2. Paste a blog article URL
3. Click "Generate Video"
4. Wait for the video to process (this may take 2-5 minutes)
5. Download your video!

## Important Notes for FREE Tier

⚠️ **Free Tier Limitations:**

1. **Services spin down after 15 minutes of inactivity**
   - First request after inactivity may take 30-60 seconds (cold start)
   - Subsequent requests are fast

2. **750 hours/month per service**
   - More than enough for development and testing
   - Resets monthly

3. **Build time limits**
   - Builds must complete within 15 minutes (yours will!)

4. **Disk space**
   - 1GB storage (plenty for your app)

## Troubleshooting

### "Service failed to start"
- Check that REDIS_URL is set correctly
- Verify your Redis instance is accessible

### "Cannot connect to Redis"
- Make sure you're using the correct Redis URL format
- For Upstash, use the `rediss://` URL (with double 's')
- Check if your Redis instance has password authentication enabled

### "Groq API error"
- Verify your GROQ_API_KEY is correct (should start with `gsk_`)
- Check you haven't exceeded Groq's free tier rate limits
- Make sure you created the API key at https://console.groq.com/keys

### "Video generation fails"
- Check that PEXELS_API_KEY is set
- Verify you haven't exceeded Pexels rate limits

### Frontend can't connect to backend
- Make sure VITE_API_URL points to your backend service URL
- Check CORS settings in backend (already configured to allow all origins)

## Monitoring Your App

- **Render Dashboard**: View logs, metrics, and service status
- **Free tier includes**: Basic metrics and logs
- **Logs**: Click on any service → "Logs" tab to see real-time output

## Upgrading Later (Optional)

If you need more resources later:
- **Starter ($7/month)**: No cold starts, stays always running
- **Standard ($25/month)**: More CPU, RAM, and bandwidth

But for testing and moderate use, **FREE tier works great**! 🚀

## Cost Breakdown

| Service | Cost |
|---------|------|
| Render Web Service (API) | **FREE** |
| Render Worker Service | **FREE** |
| Render Static Site (Frontend) | **FREE** |
| Redis (Upstash/Railway) | **FREE** |
| Groq AI (LLM) | **FREE** ✨ |
| Edge TTS (Voiceover) | **FREE** ✨ |
| Pexels (Stock Videos) | **FREE** ✨ |
| **TOTAL** | **$0/month** 🎉 |

**Everything is 100% FREE!** No hidden costs, no credit card required for AI services!

## Next Steps

- Set up custom domain (free with Render)
- Add user authentication
- Implement video queue management
- Add more video templates
- Configure webhooks for notifications

Happy deploying! 🎬
