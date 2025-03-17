import os
from flask import Flask, request, jsonify
import requests
import base64
from pydub import AudioSegment
import tempfile
from pathlib import Path
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv('GOOGLE_API_KEY')
BASE_URL = "https://speech.googleapis.com/v1/speech:recognize"

def convert_to_wav(audio_file, target_path):
    """Convert audio to WAV format with correct parameters"""
    audio = AudioSegment.from_file(audio_file)
    audio = audio.set_channels(1)  # Convert to mono
    audio = audio.set_frame_rate(16000)  # Set sample rate to 16kHz
    audio.export(target_path, format="wav")
    return target_path

def transcribe_audio(audio_path, language_code="ru-RU"):
    """Transcribe audio using Google Cloud Speech-to-Text API"""
    # Read and encode the audio file
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
    audio_content = base64.b64encode(content).decode('utf-8')
    
    # Prepare request
    url = f"{BASE_URL}?key={API_KEY}"
    data = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": 16000,
            "languageCode": language_code,
            "enableAutomaticPunctuation": True,
            "model": "default",
            "useEnhanced": True
        },
        "audio": {
            "content": audio_content
        }
    }
    
    # Make request
    response = requests.post(url, json=data)
    
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")
    
    result = response.json()
    
    # Process results
    results = []
    for result in result.get('results', []):
        for alternative in result.get('alternatives', []):
            results.append({
                "transcript": alternative.get('transcript', ''),
                "confidence": alternative.get('confidence', 0)
            })
    
    return results

@app.route("/transcribe", methods=["POST"])
def handle_transcribe():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        # Get language code from request, default to Russian
        language = request.form.get("language", "ru-RU")
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save original file
            orig_path = temp_path / "original"
            file.save(orig_path)
            
            # Convert to proper WAV format
            wav_path = temp_path / "processed.wav"
            convert_to_wav(orig_path, wav_path)
            
            # Transcribe
            results = transcribe_audio(wav_path, language)
            
            return jsonify({
                "success": True,
                "results": results
            })
    
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
