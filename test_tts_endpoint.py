import os
import sys
import asyncio
import aiohttp
import json
import base64
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8181"
TEXT = "안녕하세요, 테스트 음성입니다."
VOICE_ID = "Korean_SassyGirl"

async def test_tts_post():
    """Test the POST /api/tts/ endpoint"""
    url = f"{BASE_URL}/api/tts/"
    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    
    # Timeout configuration
    timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds total timeout
    
    payload = {
        "text": TEXT,
        "voice_id": VOICE_ID,
        "speed": 1.0,
        "vol": 1.0,
        "audio_sample_rate": 24000,
        "bitrate": 128000,
        "format": "mp3"
    }
    
    print(f"\n=== Testing POST {url} ===")
    print(f"Request headers: {headers}")
    print(f"Request payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                print(f"\nResponse status: {response.status}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"\n=== Response Details ===")
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print(f"Response Headers: {dict(response.headers)}")
                
                # Read response content
                response_content = await response.read()
                print(f"Response length: {len(response_content)} bytes")
                
                try:
                    # Try to decode as JSON if possible
                    response_json = json.loads(response_content)
                    print("\n🔍 JSON Response:")
                    print(json.dumps(response_json, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    # If not JSON, print as text
                    response_text = response_content.decode('utf-8', errors='replace')
                    print(f"\n🔍 Text Response (first 1000 chars):\n{response_text[:1000]}\n...")
                
                if response.status == 200:
                    
                    try:
                        # Get the response text first
                        response_text = await response.text()
                    
                        try:
                            # Try to parse as JSON
                            response_json = json.loads(response_text)
                            print(f"✅ Parsed JSON response: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
                            
                            # Check if audio_file exists in response
                            if 'audio_file' in response_json:
                                # Decode base64 audio data
                                import base64
                                audio_data = base64.b64decode(response_json['audio_file'])
                                with open("tts_output_post.mp3", "wb") as f:
                                    f.write(audio_data)
                                print(f"✅ Audio saved as 'tts_output_post.mp3' ({len(audio_data)} bytes)")
                                return True
                            else:
                                print("❌ No 'audio_file' field in the API response")
                                if 'base_resp' in response_json and 'status_msg' in response_json['base_resp']:
                                    print(f"Error details: {response_json['base_resp']['status_msg']}")
                                return False
                            
                        except json.JSONDecodeError:
                            # If not JSON, try to save as raw audio
                            print("⚠️ Response is not JSON. Saving as raw audio...")
                            with open("tts_output_post.raw", "wb") as f:
                                f.write(response_content)
                            print(f"⚠️ Saved raw response to 'tts_output_post.raw' ({len(response_content)} bytes)")
                            return False
                    except Exception as e:
                        logger.error(f"Exception: {str(e)}")
                        print(f"❌ Exception: {str(e)}")
                        return False
                    error_text = await response.text()
                    print(f"❌ Error (Status {response.status}): {error_text}")
                    try:
                        error_json = await response.json()
                        print(f"Error details: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"Raw error response: {error_text}")
                    return False
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"❌ Exception: {str(e)}")
        return False

async def test_tts_get():
    """Test the GET /api/tts/generate endpoint"""
    params = {
        "text": TEXT,
        "voice_id": VOICE_ID,
        "speed": 1.0,
        "vol": 1.0,
        "audio_sample_rate": 24000,
        "bitrate": 128000,
        "format": "mp3"
    }
    
    # Timeout configuration
    timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds total timeout
    
    url = f"{BASE_URL}/api/tts/generate"
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"\nTesting GET {url}")
            print(f"Query params: {params}")
            
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                
                if response.status == 200:
                    # Save the audio file
                    audio_data = await response.read()
                    output_file = "tts_output_get.mp3"
                    with open(output_file, "wb") as f:
                        f.write(audio_data)
                    print(f"✅ Audio saved as '{output_file}' ({len(audio_data)} bytes)")
                    
                    # Check if the file is a valid MP3
                    if len(audio_data) < 100:  # Very small file likely indicates an error
                        print(f"⚠️ Warning: The generated audio file is very small ({len(audio_data)} bytes) and may be invalid")
                        with open(output_file + ".txt", "w", encoding="utf-8") as f:
                            f.write(f"Response headers: {dict(response.headers)}\n")
                            f.write(f"Response content: {audio_data[:500]}\n")  # First 500 bytes
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Error (Status {response.status}): {error_text}")
                    try:
                        error_json = await response.json()
                        print(f"Error details: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"Raw error response: {error_text}")
                    return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

async def main():
    print("=== Testing TTS Endpoints ===")
    print(f"Base URL: {BASE_URL}\n")
    
    # Check required environment variables
    required_vars = ["MINIMAX_API_KEY", "MINIMAX_GROUP_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    # Print environment info for debugging
    print("\nEnvironment Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value and len(value) > 10:  # Truncate long values
            value = f"{value[:5]}...{value[-5:]}"
        print(f"  {var}: {'✅ Set' if value else '❌ Missing'}")
        if value:
            print(f"     Value: {value}")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease create a .env file with these variables.")
        return
    
    print("✅ Environment variables check passed")
    
    # Test POST endpoint
    print("\n--- Testing POST /api/tts/ ---")
    post_success = await test_tts_post()
    
    # Test GET endpoint
    print("\n--- Testing GET /api/tts/generate ---")
    get_success = await test_tts_get()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"POST /api/tts/: {'✅ Success' if post_success else '❌ Failed'}")
    print(f"GET /api/tts/generate: {'✅ Success' if get_success else '❌ Failed'}")

if __name__ == "__main__":
    asyncio.run(main())
