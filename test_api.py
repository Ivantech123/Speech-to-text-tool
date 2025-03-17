import os
import requests
import json
import wave
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('GOOGLE_API_KEY')
BASE_URL = "https://speech.googleapis.com/v1/speech:recognize"

def test_credentials():
    """Test if Google Cloud credentials are working"""
    try:
        # Make a simple request to test the API key
        url = f"{BASE_URL}?key={API_KEY}"
        response = requests.post(url, 
            json={
                "config": {
                    "languageCode": "ru-RU"
                },
                "audio": {
                    "content": ""
                }
            }
        )
        if response.status_code == 400:  # Expected for empty audio
            print("✅ Successfully validated API key")
            return True
        else:
            print(f"❌ API key validation failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing API key: {str(e)}")
        return False

def create_test_wav():
    """Create a simple test WAV file"""
    filename = "test.wav"
    
    # Create a simple WAV file (1 second of silence)
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b'\x00' * 32000)
    
    print(f"✅ Created test file: {filename}")
    return filename

def test_transcription(file_path):
    """Test transcription with a simple audio file"""
    try:
        # Read the audio file
        with open(file_path, "rb") as audio_file:
            content = audio_file.read()
        
        # Encode audio content in base64
        import base64
        audio_content = base64.b64encode(content).decode('utf-8')
        
        # Prepare request
        url = f"{BASE_URL}?key={API_KEY}"
        data = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": "ru-RU",
                "enableAutomaticPunctuation": True
            },
            "audio": {
                "content": audio_content
            }
        }
        
        # Make request
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            print("✅ Successfully made API call to Google Speech-to-Text")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ API call failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing transcription: {str(e)}")
        return False

def cleanup(test_file):
    """Clean up test files"""
    try:
        os.remove(test_file)
        print(f"✅ Cleaned up test file: {test_file}")
    except:
        print(f"❌ Could not remove test file: {test_file}")

def main():
    print("🔍 Testing Google Cloud Speech-to-Text API")
    print("-" * 50)
    
    # Test 1: Check credentials
    print("\n1. Testing credentials...")
    if not test_credentials():
        print("❌ Failed credential test. Please check your Google Cloud setup.")
        return
    
    # Test 2: Create and test with sample file
    print("\n2. Testing transcription...")
    test_file = create_test_wav()
    test_result = test_transcription(test_file)
    cleanup(test_file)
    
    if test_result:
        print("\n✨ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
