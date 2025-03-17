# Voice Transcription Server

This is a Flask server that provides voice transcription services using Google Cloud Speech-to-Text API. It's designed for easy integration with chat systems and supports multiple audio formats.

## Features
- Automatic audio format conversion to optimal settings
- Support for multiple languages (default: Russian)
- Returns confidence scores for transcriptions
- Handles multiple audio formats (mp3, wav, ogg, etc.)

## Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Set up Google Cloud credentials:
   - Create a Google Cloud project
   - Enable Speech-to-Text API
   - Create a service account and download the JSON key file
   - Set the environment variable:
     ```bash
     set GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
     ```

## Running the Server

Start the server:
```bash
python server.py
```

The server will run on `http://localhost:5000` by default.

## API Usage

### Transcribe Audio

**Endpoint:** `POST /transcribe`

**Parameters:**
- `file`: Audio file (multipart/form-data)
- `language`: Language code (optional, defaults to "ru-RU")

**Example using curl:**
```bash
curl -X POST -F "file=@audio.mp3" -F "language=ru-RU" http://localhost:5000/transcribe
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "transcript": "Transcribed text here",
      "confidence": 0.98
    }
  ]
}
```

## Integration Example

Python example to send audio to the server:
```python
import requests

def transcribe_audio(file_path, language="ru-RU"):
    url = "http://localhost:5000/transcribe"
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"language": language}
        response = requests.post(url, files=files, data=data)
    return response.json()
