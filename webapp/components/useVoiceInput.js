import { useState, useEffect, useRef } from 'react'

// Note: Vapi integration will be implemented once environment variables are set up
export const useVoiceInput = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [isVapiEnabled, setIsVapiEnabled] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState(null)
  
  const vapiRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const streamRef = useRef(null)

  // Check if Vapi is available
  useEffect(() => {
    const apiKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY
    if (apiKey && apiKey !== 'your_vapi_public_key_here') {
      setIsVapiEnabled(true)
      initializeVapi(apiKey)
    } else {
      console.log('Vapi not configured - using browser speech recognition as fallback')
      initializeBrowserSpeechRecognition()
    }
  }, [])

  const initializeVapi = async (apiKey) => {
    try {
      // Dynamic import of Vapi to avoid SSR issues
      const { default: Vapi } = await import('@vapi-ai/web')
      
      vapiRef.current = new Vapi(apiKey)
      
      // Set up Vapi event listeners
      vapiRef.current.on('speech-start', () => {
        console.log('Speech started')
        setIsRecording(true)
      })
      
      vapiRef.current.on('speech-end', () => {
        console.log('Speech ended')
        setIsRecording(false)
      })
      
      vapiRef.current.on('message', (message) => {
        if (message.type === 'transcript' && message.transcript) {
          setTranscript(message.transcript)
        }
      })
      
      vapiRef.current.on('error', (error) => {
        console.error('Vapi error:', error)
        setError(error.message || 'Voice input error')
        setIsRecording(false)
      })
      
      console.log('Vapi initialized successfully')
    } catch (error) {
      console.error('Failed to initialize Vapi:', error)
      setError('Failed to initialize voice input')
      setIsVapiEnabled(false)
      // Fallback to browser speech recognition
      initializeBrowserSpeechRecognition()
    }
  }

  const initializeBrowserSpeechRecognition = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Speech recognition not supported in this browser')
      return
    }

    console.log('Using browser speech recognition as fallback')
  }

  const startRecording = async () => {
    try {
      setError(null)
      setTranscript('')

      if (isVapiEnabled && vapiRef.current) {
        // Use Vapi for voice input
        await vapiRef.current.start()
      } else {
        // Use browser Speech Recognition API as fallback
        await startBrowserSpeechRecognition()
      }
    } catch (error) {
      console.error('Error starting recording:', error)
      setError('Failed to start voice recording')
      setIsRecording(false)
    }
  }

  const stopRecording = async () => {
    try {
      if (isVapiEnabled && vapiRef.current) {
        await vapiRef.current.stop()
      } else {
        stopBrowserSpeechRecognition()
      }
      setIsRecording(false)
    } catch (error) {
      console.error('Error stopping recording:', error)
      setError('Failed to stop voice recording')
      setIsRecording(false)
    }
  }

  const startBrowserSpeechRecognition = async () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    
    if (!SpeechRecognition) {
      throw new Error('Speech recognition not supported')
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      setIsRecording(true)
      console.log('Browser speech recognition started')
    }

    recognition.onresult = (event) => {
      let finalTranscript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript
        }
      }
      if (finalTranscript) {
        setTranscript(finalTranscript.trim())
      }
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setError(`Speech recognition error: ${event.error}`)
      setIsRecording(false)
    }

    recognition.onend = () => {
      setIsRecording(false)
      console.log('Browser speech recognition ended')
    }

    recognition.start()
    mediaRecorderRef.current = recognition
  }

  const stopBrowserSpeechRecognition = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current = null
    }
  }

  const toggleRecording = async () => {
    if (isRecording) {
      await stopRecording()
    } else {
      await startRecording()
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (vapiRef.current) {
        vapiRef.current.stop().catch(console.error)
      }
      if (mediaRecorderRef.current) {
        stopBrowserSpeechRecognition()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  return {
    isRecording,
    isVapiEnabled,
    transcript,
    error,
    startRecording,
    stopRecording,
    toggleRecording,
    clearTranscript: () => setTranscript(''),
    clearError: () => setError(null)
  }
} 