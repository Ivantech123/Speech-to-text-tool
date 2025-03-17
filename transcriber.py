import os
from pathlib import Path
import json
import soundfile as sf
from google.cloud import speech

def transcribe_audio(audio_file_path):
    """
    Transcribe an audio file to text using Google Cloud Speech-to-Text API
    """
    # Check if file exists
    if not Path(audio_file_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
    
    # Initialize the client
    client = speech.SpeechClient()
    
    # Read the audio file
    with open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
    
    # Create the audio object
    audio = speech.RecognitionAudio(content=content)
    
    # Configure the recognition settings
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ru-RU",  # Russian language
        enable_automatic_punctuation=True,
    )
    
    # Perform the transcription
    response = client.recognize(config=config, audio=audio)
    
    # Combine all transcriptions
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "
    
    # Create output JSON
    output = {
        "audio_file": audio_file_path,
        "transcript": transcript.strip(),
        "timestamp": str(Path(audio_file_path).stat().st_mtime),
        "confidence": response.results[0].alternatives[0].confidence if response.results else None
    }
    
    # Save to JSON file
    output_path = Path(audio_file_path).with_suffix('.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    return output

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python transcriber.py <path_to_audio_file>")
        sys.exit(1)
    
    try:
        result = transcribe_audio(sys.argv[1])
        print(f"Transcription completed successfully!")
        print(f"Transcript saved to: {Path(sys.argv[1]).with_suffix('.json')}")
        print(f"Confidence: {result['confidence']}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
