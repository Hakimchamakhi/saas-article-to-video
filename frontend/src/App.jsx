import { useState, useEffect, useRef } from 'react'

// Use environment variable for API URL, fallback to relative path for local dev
const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'
const POLL_INTERVAL = 5000 // Poll every 5 seconds

function App() {
  const [url, setUrl] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [videoUrl, setVideoUrl] = useState(null)
  const [progress, setProgress] = useState('')
  const pollingIntervalRef = useRef(null)

  // Log API configuration on mount
  useEffect(() => {
    console.log('API Base URL:', API_BASE_URL)
    console.log('VITE_API_URL env var:', import.meta.env.VITE_API_URL || 'not set')
  }, [])

  // Clean up polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  // Poll for job status
  const pollJobStatus = async (currentJobId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/status/${currentJobId}`)

      if (!response.ok) {
        throw new Error('Failed to fetch job status')
      }

      const data = await response.json()
      setStatus(data.status)
      setProgress(data.progress || '')

      if (data.status === 'complete') {
        // Stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }

        setVideoUrl(data.video_url)
        setIsProcessing(false)
        setError(null)
      } else if (data.status === 'failed') {
        // Stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }

        setError(data.error || 'Video generation failed')
        setIsProcessing(false)
      }
    } catch (err) {
      console.error('Error polling job status:', err)
      // Don't stop polling on network errors, just log them
    }
  }

  // Start polling when we have a job ID
  useEffect(() => {
    if (jobId && isProcessing) {
      // Poll immediately
      pollJobStatus(jobId)

      // Then poll every POLL_INTERVAL
      pollingIntervalRef.current = setInterval(() => {
        pollJobStatus(jobId)
      }, POLL_INTERVAL)
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [jobId, isProcessing])

  const handleGenerateVideo = async (e) => {
    e.preventDefault()

    // Reset state
    setError(null)
    setVideoUrl(null)
    setStatus(null)
    setProgress('')

    // Validate URL
    if (!url.trim()) {
      setError('Please enter a valid URL')
      return
    }

    try {
      setIsProcessing(true)

      const response = await fetch(`${API_BASE_URL}/generate-video`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url.trim() }),
      })

      if (!response.ok) {
        // Try to get error details
        const contentType = response.headers.get('content-type')
        let errorMessage = `Server error: ${response.status} ${response.statusText}`

        if (contentType && contentType.includes('application/json')) {
          try {
            const errorData = await response.json()
            errorMessage = errorData.detail || errorMessage
          } catch (e) {
            // JSON parsing failed, use default message
          }
        } else {
          // Non-JSON response, might be HTML error page
          const textResponse = await response.text()
          console.error('Non-JSON response:', textResponse)
          errorMessage += '\n\nCheck backend logs for details. Make sure GROQ_API_KEY, PEXELS_API_KEY, and REDIS_URL are configured.'
        }

        throw new Error(errorMessage)
      }

      const data = await response.json()
      setJobId(data.job_id)
      setStatus('pending')
      setProgress('Initializing...')
    } catch (err) {
      console.error('Error generating video:', err)
      setError(err.message)
      setIsProcessing(false)
    }
  }

  const handleReset = () => {
    setUrl('')
    setJobId(null)
    setStatus(null)
    setError(null)
    setVideoUrl(null)
    setProgress('')
    setIsProcessing(false)

    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Blog to Video Converter
          </h1>
          <p className="text-xl text-gray-600">
            Transform any blog article into an engaging video with AI-powered voiceover and stock footage
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          {!videoUrl ? (
            <>
              {/* Input Form */}
              <form onSubmit={handleGenerateVideo} className="mb-6">
                <label htmlFor="url-input" className="block text-sm font-semibold text-gray-700 mb-2">
                  Article URL
                </label>
                <div className="flex gap-3">
                  <input
                    id="url-input"
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com/blog-post"
                    disabled={isProcessing}
                    className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900"
                    required
                  />
                  <button
                    type="submit"
                    disabled={isProcessing}
                    className="px-8 py-3 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200"
                  >
                    {isProcessing ? 'Processing...' : 'Generate Video'}
                  </button>
                </div>
              </form>

              {/* Status Display */}
              {isProcessing && (
                <div className="mt-8 p-6 bg-blue-50 rounded-lg border-2 border-blue-200">
                  <div className="flex items-start gap-4">
                    {/* Animated Spinner */}
                    <div className="flex-shrink-0">
                      <svg
                        className="animate-spin h-8 w-8 text-primary-600"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                    </div>

                    {/* Status Text */}
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {status === 'pending' && 'Queued...'}
                        {status === 'processing' && 'Processing...'}
                      </h3>
                      <p className="text-gray-700">
                        {progress || 'Please wait while we generate your video. This may take a few minutes.'}
                      </p>
                      <div className="mt-4 text-sm text-gray-600">
                        <p className="mb-1">The process includes:</p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>Scraping and analyzing the article</li>
                          <li>Generating video script with AI</li>
                          <li>Creating voiceover narration</li>
                          <li>Finding relevant stock footage</li>
                          <li>Assembling the final video</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Display */}
              {error && (
                <div className="mt-8 p-6 bg-red-50 rounded-lg border-2 border-red-200">
                  <div className="flex items-start gap-3">
                    <svg
                      className="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-red-900 mb-1">Error</h3>
                      <p className="text-red-800">{error}</p>
                    </div>
                  </div>
                  <button
                    onClick={handleReset}
                    className="mt-4 px-4 py-2 bg-red-100 text-red-700 font-medium rounded-lg hover:bg-red-200 transition-colors duration-200"
                  >
                    Try Again
                  </button>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Success State - Video Display */}
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                  <svg
                    className="w-8 h-8 text-green-600"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M5 13l4 4L19 7"></path>
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Video Generated Successfully!
                </h2>
                <p className="text-gray-600">
                  Your video is ready. Watch it below or download it to your device.
                </p>
              </div>

              {/* Video Player */}
              <div className="mb-6 rounded-lg overflow-hidden bg-black">
                <video
                  controls
                  className="w-full"
                  src={videoUrl}
                >
                  Your browser does not support the video tag.
                </video>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 justify-center">
                <a
                  href={videoUrl}
                  download
                  className="px-6 py-3 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors duration-200"
                >
                  Download Video
                </a>
                <button
                  onClick={handleReset}
                  className="px-6 py-3 bg-gray-200 text-gray-800 font-semibold rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors duration-200"
                >
                  Generate Another
                </button>
              </div>
            </>
          )}
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-primary-600"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">AI-Powered</h3>
            <p className="text-gray-600 text-sm">
              Advanced GPT technology summarizes your content into engaging video scripts
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-primary-600"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Stock Footage</h3>
            <p className="text-gray-600 text-sm">
              Automatically finds and integrates relevant, high-quality stock videos
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-primary-600"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Voice Narration</h3>
            <p className="text-gray-600 text-sm">
              Professional AI voiceover brings your content to life with natural speech
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-gray-600 text-sm">
          <p>Powered by Groq AI (FREE), Edge TTS (FREE), Pexels (FREE), and MoviePy</p>
        </div>
      </div>
    </div>
  )
}

export default App
