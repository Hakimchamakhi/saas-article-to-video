# Blog to Video Converter 🎬

A full-stack web application that automatically converts blog articles into engaging short videos with AI-generated voiceovers and relevant stock footage - **100% FREE APIs!**

> No credit card required! Uses Groq AI (FREE), Google TTS (FREE), and Pexels (FREE)

## Features

- **AI-Powered Script Generation**: Uses Groq AI (FREE!) with Llama 3.3 to summarize articles into video scripts
- **Professional Voiceover**: Leverages Google Text-to-Speech (FREE!) for natural-sounding narration
- **Automatic Stock Footage**: Finds and integrates relevant stock videos from Pexels (FREE!)
- **Asynchronous Processing**: Uses Celery and Redis for efficient background task processing
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- **Real-time Progress**: Live status updates during video generation
- **100% Free APIs**: No credit card required for AI services!

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for Python
- **Celery**: Distributed task queue for async processing
- **Redis**: Message broker and result backend
- **Groq API**: Fast, free LLM API (Llama 3.3) for script generation
- **Google TTS (gTTS)**: Free Google text-to-speech for voiceover
- **Pexels API**: Free stock video footage
- **MoviePy**: Video editing and assembly
- **Newspaper3k**: Article scraping and parsing

### Frontend
- **React**: UI library
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application and API endpoints
│   ├── worker.py            # Celery worker and video generation task
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (create from .env.example)
│   ├── .env.example         # Template for environment variables
│   └── static/              # Generated video files
│
└── frontend/
    ├── src/
    │   ├── App.jsx          # Main React component
    │   ├── main.jsx         # React entry point
    │   └── index.css        # Global styles with Tailwind directives
    ├── index.html           # HTML template
    ├── package.json         # Node dependencies
    ├── vite.config.js       # Vite configuration
    ├── tailwind.config.js   # Tailwind CSS configuration
    └── postcss.config.js    # PostCSS configuration
```

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+**
- **Node.js 16+** and npm
- **Redis** (for Celery broker)
- **FFmpeg** (required by MoviePy for video processing)

### Installing Prerequisites

#### macOS
```bash
brew install python node redis ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip nodejs npm redis-server ffmpeg
```

#### Windows
- Install Python from [python.org](https://www.python.org/)
- Install Node.js from [nodejs.org](https://nodejs.org/)
- Install Redis from [redis.io](https://redis.io/download) or use Windows Subsystem for Linux (WSL)
- Install FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)

## API Keys Required (All 100% FREE!)

You'll need to obtain API keys for the following services:

1. **Groq API Key** (FREE - No Credit Card!)
   - Sign up at [Groq Console](https://console.groq.com/)
   - Create an API key at [API Keys](https://console.groq.com/keys)
   - Completely free with generous rate limits
   - No credit card required!

2. **Pexels API Key** (FREE)
   - Sign up at [Pexels](https://www.pexels.com/)
   - Get your API key at [Pexels API](https://www.pexels.com/api/)
   - The API is completely free (200 requests/hour)

**Note**: Google TTS requires no API key - it's built-in and completely free!

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd saas-article-to-video
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# GROQ_API_KEY=your_groq_api_key_here
# PEXELS_API_KEY=your_pexels_api_key_here
# REDIS_URL=redis://localhost:6379/0
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node dependencies
npm install
```

### 4. Start Redis

Make sure Redis is running on your system:

```bash
# macOS/Linux
redis-server

# Or if installed as a service:
# macOS
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis-server
```

Verify Redis is running:
```bash
redis-cli ping
# Should respond with: PONG
```

## Running the Application

You need to run three services simultaneously. Open three separate terminal windows:

### Terminal 1: Backend API Server

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

The API will be available at `http://localhost:8000`

### Terminal 2: Celery Worker

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
celery -A worker.celery_app worker --loglevel=info
```

The worker will process video generation tasks.

### Terminal 3: Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Paste a blog article URL into the input field
3. Click "Generate Video"
4. Wait while the system:
   - Scrapes the article content
   - Generates an AI video script
   - Creates professional voiceover
   - Downloads relevant stock footage
   - Assembles the final video
5. Watch or download your generated video!

## How It Works

### Workflow

1. **User Input**: User submits a blog article URL through the React frontend
2. **Task Creation**: FastAPI creates a Celery task and returns a job ID
3. **Status Polling**: Frontend polls the status endpoint every 5 seconds
4. **Background Processing**: Celery worker executes the video generation pipeline:
   - Scrapes article text using Newspaper3k
   - Summarizes content into a video script using Groq AI (Llama 3.1)
   - Generates voiceover using Google TTS (FREE!)
   - Searches and downloads stock videos from Pexels
   - Assembles video clips with audio using MoviePy
5. **Completion**: When done, the video URL is returned to the frontend
6. **Playback**: User can watch or download the generated video

### API Endpoints

- `POST /api/generate-video`: Initiates video generation (returns job_id)
- `GET /api/status/{job_id}`: Check task status (pending/processing/complete/failed)
- `GET /api/download/{filename}`: Serve generated video file

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError` for Python packages
- **Solution**: Ensure you're in the virtual environment and have run `pip install -r requirements.txt`

**Issue**: Redis connection error
- **Solution**: Make sure Redis is running (`redis-cli ping` should return `PONG`)

**Issue**: FFmpeg not found
- **Solution**: Install FFmpeg and ensure it's in your system PATH

**Issue**: Groq API errors
- **Solution**: Verify your API key is correct (starts with `gsk_`) and check rate limits

**Issue**: No videos found from Pexels
- **Solution**: Check your Pexels API key and ensure you're not hitting rate limits

**Issue**: Video generation fails
- **Solution**: Check the Celery worker logs for detailed error messages

### Celery Worker Logs

Monitor the Celery worker terminal for detailed progress and error messages. The worker provides step-by-step updates:
- Scraping article content
- Generating video script
- Creating voiceover
- Downloading stock footage
- Assembling video

## Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use secure secret management
2. **CORS**: Update CORS settings in `backend/main.py` to specify your frontend domain
3. **Process Manager**: Use Supervisor or systemd for managing backend processes
4. **Reverse Proxy**: Use Nginx or Apache as a reverse proxy
5. **Static Files**: Serve static files through a CDN
6. **Scaling**: Add more Celery workers for concurrent video processing
7. **Monitoring**: Implement logging and monitoring (e.g., Sentry, Prometheus)
8. **Queue Management**: Consider using Flower for Celery monitoring

## Cost Considerations

### API Usage Costs

**🎉 100% FREE! 🎉**

- **Groq AI (Llama 3.3)**: FREE with generous rate limits (no credit card required!)
- **Google TTS**: Completely FREE (no API key needed)
- **Pexels**: FREE (200 requests/hour)

**Estimated cost per video**: $0.00

### Why This Stack is Amazing

- **No Credit Card Required**: All APIs are completely free
- **No Hidden Costs**: Zero surprises on your bill
- **Production Ready**: Free tier is suitable for real applications
- **Rate Limits**: Groq provides generous free tier limits
- **No Expiration**: Services remain free indefinitely

## Limitations

- Video generation takes 2-5 minutes depending on article length
- Stock footage quality depends on Pexels search results
- Maximum recommended article length: ~2000 words
- Generated videos are typically 30-90 seconds long

## Future Enhancements

Potential improvements:
- User authentication and video history
- Custom voice selection
- Multiple video style templates
- Background music integration
- Subtitle/caption generation
- Video length customization
- Batch processing multiple articles
- Social media integration (auto-post to YouTube, etc.)

## License

This project is provided as-is for educational and commercial use.

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

## Credits

- **Groq** for free, fast LLM API (Llama models)
- **Google** for Google TTS (free text-to-speech)
- **Pexels** for free stock video footage
- **MoviePy** for video processing
- **FastAPI** for the backend framework
- **React** for the frontend framework
