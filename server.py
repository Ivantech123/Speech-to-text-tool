import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import base64
from pydub import AudioSegment
import tempfile
from pathlib import Path
import logging
from dotenv import load_dotenv
import time
from functools import wraps
import redis
from google.cloud import speech_v1p1beta1 as speech
from google.oauth2 import service_account
import io
import wave
import soundfile as sf
import numpy as np
from werkzeug.utils import secure_filename
import validators

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

# Configuration class
class Config:
    API_KEY = os.getenv('GOOGLE_API_KEY')
    BASE_URL = "https://speech.googleapis.com/v1/speech:recognize"
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    UPLOAD_FOLDER = '/tmp/audio_uploads'
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'wma', 'opus'}
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Performance settings
    THREAD_POOL_SIZE = int(os.getenv('THREAD_POOL_SIZE', '4'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '300'))  # 5 minutes
    
    # Audio processing settings
    SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', '16000'))
    CHANNELS = int(os.getenv('CHANNELS', '1'))

app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Initialize Redis for caching
try:
    redis_client = redis.from_url(Config.REDIS_URL)
except:
    redis_client = None
    app.logger.warning("Redis connection failed, proceeding without caching")

# Initialize thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=Config.THREAD_POOL_SIZE)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def validate_language_code(lang_code):
    """Validate language code format"""
    if not lang_code or not isinstance(lang_code, str):
        return False
    # Basic validation - could be expanded
    return len(lang_code) >= 2 and '-' in lang_code

def cache_result(key, ttl=3600):
    """Decorator to cache function results in Redis"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if redis_client:
                try:
                    cached_result = redis_client.get(key)
                    if cached_result:
                        app.logger.info(f"Cache hit for key: {key}")
                        return eval(cached_result.decode('utf-8'))
                except Exception as e:
                    app.logger.warning(f"Cache get error: {e}")
            
            result = func(*args, **kwargs)
            
            if redis_client:
                try:
                    redis_client.setex(key, ttl, str(result))
                    app.logger.info(f"Result cached for key: {key}")
                except Exception as e:
                    app.logger.warning(f"Cache set error: {e}")
            
            return result
        return wrapper
    return decorator

def measure_time(func):
    """Decorator to measure execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        app.logger.info(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

def convert_to_wav(audio_file, target_path, sample_rate=16000, channels=1):
    """Convert audio to WAV format with correct parameters"""
    try:
        # Load audio file
        audio = AudioSegment.from_file(audio_file)
        
        # Apply transformations
        audio = audio.set_channels(channels)
        audio = audio.set_frame_rate(sample_rate)
        
        # Export to WAV
        audio.export(target_path, format="wav")
        return target_path
    except Exception as e:
        app.logger.error(f"Audio conversion error: {e}")
        raise

def transcribe_with_google_client(audio_path, language_code="ru-RU", config_options=None):
    """Transcribe audio using Google Cloud Speech-to-Text client library with enhanced options"""
    try:
        # Load credentials from file if available
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            client = speech.SpeechClient(credentials=credentials)
        else:
            # Fallback to API key method
            client = speech.SpeechClient()
        
        # Read audio file
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()
        
        # Configure request
        audio = speech.RecognitionAudio(content=content)
        
        # Default configuration
        recognition_config = {
            "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "sample_rate_hertz": Config.SAMPLE_RATE,
            "language_code": language_code,
            "enable_automatic_punctuation": True,
            "model": "default",
            "use_enhanced": True,
            "enable_word_time_offsets": True,
            "enable_speaker_diarization": True,
            "diarization_speaker_count": 2,
        }
        
        # Override with custom options if provided
        if config_options:
            recognition_config.update(config_options)
        
        config = speech.RecognitionConfig(**recognition_config)
        
        # Perform transcription
        response = client.recognize(config=config, audio=audio)
        
        # Process results
        results = []
        for result in response.results:
            alternatives = []
            for alternative in result.alternatives:
                alternatives.append({
                    "transcript": alternative.transcript,
                    "confidence": alternative.confidence,
                    "words": [
                        {
                            "word": word_info.word,
                            "start_time": float(word_info.start_time.total_seconds()),
                            "end_time": float(word_info.end_time.total_seconds())
                        }
                        for word_info in alternative.words
                    ] if hasattr(alternative, 'words') else []
                })
            results.append({
                "alternatives": alternatives,
                "channel_tag": result.channel_tag if hasattr(result, 'channel_tag') else None,
                "result_end_time": float(result.result_end_time.total_seconds()) if hasattr(result, 'result_end_time') else None
            })
        
        return results
        
    except Exception as e:
        app.logger.error(f"Google Speech API error: {e}")
        raise

def transcribe_audio(audio_path, language_code="ru-RU", config_options=None):
    """Transcribe audio using Google Cloud Speech-to-Text API with fallback options"""
    # Submit transcription task to thread pool for better performance
    future = executor.submit(transcribe_with_google_client, audio_path, language_code, config_options)
    return future.result()

@app.route("/", methods=["GET"])
def index():
    """Serve main page"""
    return jsonify({
        "message": "Speech-to-Text API Server",
        "version": "2.0",
        "supported_formats": list(Config.ALLOWED_EXTENSIONS),
        "max_file_size": f"{Config.MAX_CONTENT_LENGTH // (1024*1024)} MB"
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "redis_connected": bool(redis_client) if redis_client else False
    })

@app.route("/transcribe", methods=["POST"])
@measure_time
def handle_transcribe():
    """Handle transcription requests with enhanced features"""
    try:
        # Validate request
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({"error": f"File type not allowed. Allowed types: {list(Config.ALLOWED_EXTENSIONS)}"}), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        
        # Get parameters
        language = request.form.get("language", "ru-RU")
        if not validate_language_code(language):
            language = "ru-RU"  # fallback to default
        
        # Additional options
        enable_punctuation = request.form.get("punctuation", "true").lower() == "true"
        enable_profanity_filter = request.form.get("profanity_filter", "false").lower() == "true"
        enable_word_time_offsets = request.form.get("word_time_offsets", "true").lower() == "true"
        model = request.form.get("model", "default")
        
        # Create configuration based on options
        config_options = {
            "enable_automatic_punctuation": enable_punctuation,
            "profanity_filter": enable_profanity_filter,
            "enable_word_time_offsets": enable_word_time_offsets,
            "model": model,
            "use_enhanced": True
        }
        
        # Add speaker diarization if needed
        if request.form.get("speaker_diarization", "false").lower() == "true":
            config_options.update({
                "enable_speaker_diarization": True,
                "diarization_speaker_count": int(request.form.get("speaker_count", "2"))
            })
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save original file
            orig_path = temp_path / "original"
            file.save(orig_path)
            
            # Convert to proper WAV format
            wav_path = temp_path / "processed.wav"
            convert_to_wav(orig_path, wav_path, Config.SAMPLE_RATE, Config.CHANNELS)
            
            # Generate cache key
            file_hash = hash(str(orig_path) + language + str(time.time()))
            cache_key = f"transcription:{file_hash}:{language}"
            
            # Try to get cached result
            if redis_client:
                try:
                    cached_result = redis_client.get(cache_key)
                    if cached_result:
                        app.logger.info(f"Cache hit for file: {filename}")
                        return jsonify({
                            "success": True,
                            "results": eval(cached_result.decode('utf-8')),
                            "cached": True,
                            "language": language
                        })
                except Exception as e:
                    app.logger.warning(f"Cache error: {e}")
            
            # Transcribe audio
            results = transcribe_audio(wav_path, language, config_options)
            
            # Cache result if Redis is available
            if redis_client:
                try:
                    redis_client.setex(cache_key, 3600, str(results))  # Cache for 1 hour
                except Exception as e:
                    app.logger.warning(f"Cache set error: {e}")
            
            return jsonify({
                "success": True,
                "results": results,
                "language": language,
                "cached": False,
                "processing_time": time.time()
            })
    
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": int(time.time())
        }), 500

@app.route("/languages", methods=["GET"])
def supported_languages():
    """Return supported language codes"""
    languages = {
        "major_languages": [
            {"code": "en-US", "name": "English (United States)"},
            {"code": "ru-RU", "name": "Russian (Russia)"},
            {"code": "es-ES", "name": "Spanish (Spain)"},
            {"code": "fr-FR", "name": "French (France)"},
            {"code": "de-DE", "name": "German (Germany)"},
            {"code": "it-IT", "name": "Italian (Italy)"},
            {"code": "pt-BR", "name": "Portuguese (Brazil)"},
            {"code": "zh-CN", "name": "Chinese (Mandarin)"},
            {"code": "ja-JP", "name": "Japanese"},
            {"code": "ko-KR", "name": "Korean"}
        ],
        "additional_languages": [
            {"code": "af-ZA", "name": "Afrikaans"},
            {"code": "ar-SA", "name": "Arabic (Saudi Arabia)"},
            {"code": "cs-CZ", "name": "Czech"},
            {"code": "da-DK", "name": "Danish"},
            {"code": "nl-NL", "name": "Dutch"},
            {"code": "fi-FI", "name": "Finnish"},
            {"code": "el-GR", "name": "Greek"},
            {"code": "he-IL", "name": "Hebrew"},
            {"code": "hi-IN", "name": "Hindi"},
            {"code": "hu-HU", "name": "Hungarian"},
            {"code": "id-ID", "name": "Indonesian"},
            {"code": "no-NO", "name": "Norwegian"},
            {"code": "pl-PL", "name": "Polish"},
            {"code": "ro-RO", "name": "Romanian"},
            {"code": "sk-SK", "name": "Slovak"},
            {"code": "sv-SE", "name": "Swedish"},
            {"code": "tr-TR", "name": "Turkish"},
            {"code": "uk-UA", "name": "Ukrainian"}
        ]
    }
    return jsonify(languages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    host = os.environ.get("HOST", "0.0.0.0")
    
    app.logger.info(f"Starting server on {host}:{port}, debug={debug}")
    app.run(host=host, port=port, debug=debug)
