import os
import sys
import json
import time
import logging
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tts_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_API_URL = "https://api.minimax.chat/v1/t2a_v2"
DEFAULT_OUTPUT_DIR = "test_output"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Required environment variables
REQUIRED_ENV_VARS = ['MINIMAX_API_KEY', 'MINIMAX_GROUP_ID']

def validate_mp3(file_path: str) -> bool:
    """Check if a file appears to be a valid MP3."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            # Check for MP3 signature (starts with ID3 or FF followed by audio frame sync)
            return (header.startswith(b'ID3') or 
                   (len(header) > 1 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0))
    except Exception as e:
        logger.error(f"Error validating MP3 file: {e}")
        return False

def save_audio_file(content: bytes, output_path: str) -> Dict[str, Any]:
    """Save audio content to a file and return file info."""
    result = {
        'success': False,
        'file_path': output_path,
        'file_size': len(content),
        'is_valid_mp3': False,
        'error': None
    }
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        # Save the file
        with open(output_path, 'wb') as f:
            f.write(content)
        
        # Update result
        result.update({
            'success': True,
            'file_size': os.path.getsize(output_path),
            'is_valid_mp3': validate_mp3(output_path)
        })
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Error saving audio file: {e}")
    
    return result

def make_tts_request(
    text: str,
    voice_id: str = "Korean_SassyGirl",
    speed: float = 1.0,
    vol: float = 1.0,
    pitch: int = 0,
    sample_rate: int = 36000,
    bitrate: int = 128000,
    format: str = "mp3",
    max_retries: int = MAX_RETRIES
) -> Dict[str, Any]:
    """Make a TTS request to Minimax TTS v2 API with retry logic."""
    # Check required environment variables
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        return {
            'success': False,
            'error': f"Missing required environment variables: {', '.join(missing_vars)}"
        }
    
    # Prepare headers and URL
    headers = {
        "Authorization": f"Bearer {os.getenv('MINIMAX_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    url = f"{DEFAULT_API_URL}?GroupId={os.getenv('MINIMAX_GROUP_ID')}"
    
    # Prepare payload according to Minimax TTS v2 API
    payload = {
        "model": "speech-02-hd",
        "text": text,
        "timber_weights": [
            {
                "voice_id": voice_id,
                "weight": 100
            }
        ],
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "pitch": pitch,
            "vol": vol,
            "latex_read": False
        },
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": format.lower()
        },
        "language_boost": "auto"
    }
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Request headers: {headers}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            # Make the request
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            # Log response info
            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Handle non-200 responses
            if response.status_code != 200:
                error_info = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content': response.text[:1000]  # First 1000 chars of error
                }
                
                # Try to parse JSON error
                try:
                    error_info['json'] = response.json()
                    logger.error(f"API Error: {error_info['json']}")
                except:
                    logger.error(f"Raw error response: {response.text}")
                
                # Rate limiting check
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', 'unknown')
                    logger.warning(f"Rate limited. Retry after: {retry_after}")
                    if attempt < max_retries - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'error_info': error_info
                }
            
            # Check content type to determine response format
            content_type = response.headers.get('Content-Type', '')
            content = response.content
            
            # Log content type and size
            logger.info(f"Received response with Content-Type: {content_type}, Size: {len(content)} bytes")
            
            # Handle JSON response with base64-encoded audio
            if 'application/json' in content_type:
                try:
                    json_response = response.json()
                    if 'audio_file' in json_response:
                        # Decode base64 audio data
                        import base64
                        audio_data = base64.b64decode(json_response['audio_file'])
                        logger.info(f"Successfully decoded audio data: {len(audio_data)} bytes")
                        
                        # Save extra info if available
                        if 'extra_info' in json_response:
                            logger.info(f"Audio info: {json_response['extra_info']}")
                        
                        return {
                            'success': True,
                            'content': audio_data,
                            'headers': dict(response.headers),
                            'content_type': 'audio/mp3'  # Force audio/mp3 since we know it's MP3 from the API
                        }
                    else:
                        return {
                            'success': False,
                            'error': "No audio_file in JSON response",
                            'response': json_response
                        }
                except Exception as e:
                    logger.error(f"Error processing JSON response: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error processing JSON response: {str(e)}",
                        'content': content,
                        'content_type': content_type
                    }
            
            # Handle raw audio response (if the API ever returns it directly)
            return {
                'success': True,
                'content': content,
                'headers': dict(response.headers),
                'content_type': content_type
            }
            
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            logger.error(f"Request failed (attempt {attempt + 1}): {e}", exc_info=True)
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    
    # If we get here, all retries failed
    return {
        'success': False,
        'error': f"All {max_retries} attempts failed",
        'last_error': last_error
    }

def test_tts(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    text: str = "안녕하세요, 테스트 음성입니다.",
    voice_id: str = "Korean_SassyGirl",
    speed: float = 1.0,
    vol: float = 1.0,
    pitch: int = 0,
    audio_sample_rate: int = 24000,
    bitrate: int = 128000,
    format: str = "mp3"
) -> bool:
    """Test the TTS endpoint with the given parameters."""
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"tts_output_{timestamp}.{format}")
        
        # Log test configuration
        logger.info("=" * 80)
        logger.info("TTS Test Configuration:")
        logger.info(f"Output file: {output_file}")
        logger.info("\nParameters:")
        logger.info(f"  text: {text}")
        logger.info(f"  voice_id: {voice_id}")
        logger.info(f"  speed: {speed}")
        logger.info(f"  vol: {vol}")
        logger.info(f"  pitch: {pitch}")
        logger.info(f"  audio_sample_rate: {audio_sample_rate}")
        logger.info(f"  bitrate: {bitrate}")
        logger.info(f"  format: {format}")
        
        # Make the request
        logger.info("\nSending TTS request...")
        result = make_tts_request(
            text=text,
            voice_id=voice_id,
            speed=speed,
            vol=vol,
            pitch=pitch,
            sample_rate=audio_sample_rate,
            bitrate=bitrate,
            format=format
        )
        
        logger.debug(f"TTS request result keys: {list(result.keys())}")
        
        if not result.get('success', False):
            logger.error("\n TTS request failed!")
            if 'error' in result:
                logger.error(f"Error: {result['error']}")
            if 'error_info' in result:
                logger.error("\nError details:")
                logger.error(json.dumps(result.get('error_info', {}), indent=2, ensure_ascii=False))
            if 'response' in result:
                logger.error("\nFull response:")
                logger.error(json.dumps(result.get('response', {}), indent=2, ensure_ascii=False))
            return False
        
        # Check if we have content to save
        if 'content' not in result or not result['content']:
            logger.error("\n No audio content received in the response")
            logger.debug(f"Response keys: {list(result.keys())}")
            if 'response' in result:
                logger.debug(f"Response content: {result['response']}")
            return False
            
        # Save the audio file
        logger.info("\n Saving audio file...")
        try:
            with open(output_file, 'wb') as f:
                f.write(result['content'])
            
            file_size = os.path.getsize(output_file)
            logger.info("\n" + "=" * 50)
            logger.info(" TTS Test Results:")
            logger.info("-" * 50)
            logger.info(f" Audio file saved: {output_file}")
            logger.info(f"   Size: {file_size} bytes")
            
            # Validate MP3 if format is mp3
            if format.lower() == 'mp3':
                is_valid = validate_mp3(output_file)
                logger.info(f"   Valid MP3: {'' if is_valid else ''}")
            
            # Log file info
            logger.info("\nFile information:")
            logger.info(f"  Full path: {os.path.abspath(output_file)}")
            logger.info(f"  Exists: {os.path.exists(output_file)}")
            logger.info(f"  Size: {os.path.getsize(output_file)} bytes")
            
            # Try to play the file if on Windows
            if os.name == 'nt':
                try:
                    os.startfile(output_file)
                    logger.info("\n Playing the audio file...")
                except Exception as play_error:
                    logger.warning(f"Could not play audio file automatically: {play_error}")
            
            return True
            
        except Exception as save_error:
            logger.error(f"\n Failed to save audio file: {str(save_error)}", exc_info=True)
            logger.error(f"Content type: {result.get('content_type', 'unknown')}")
            logger.error(f"Content length: {len(result['content']) if 'content' in result else 0} bytes")
            
            # Try to save the raw response for debugging
            debug_file = f"{output_file}.debug"
            try:
                with open(debug_file, 'wb') as f:
                    f.write(result.get('content', b''))
                logger.error(f"Saved raw response to: {debug_file}")
            except Exception as debug_error:
                logger.error(f"Could not save debug file: {debug_error}")
            
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Unexpected error in test_tts: {str(e)}", exc_info=True)
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Minimax TTS v2 API')
    parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                      help=f'Output directory for audio files (default: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--text', type=str, default='안녕하세요, 테스트 음성입니다.',
                      help='Text to convert to speech')
    parser.add_argument('--voice-id', type=str, default='Korean_SassyGirl',
                      help='Voice ID to use (default: Korean_SassyGirl)')
    parser.add_argument('--speed', type=float, default=1.0,
                      help='Speech rate (default: 1.0)')
    parser.add_argument('--vol', type=float, default=1.0,
                      help='Volume (default: 1.0)')
    parser.add_argument('--pitch', type=int, default=0,
                      help='Pitch adjustment (-12 to 12, default: 0)')
    parser.add_argument('--audio-sample-rate', type=int, default=24000,
                      choices=[16000, 24000, 44100],
                      help='Audio sample rate in Hz (default: 24000)')
    parser.add_argument('--bitrate', type=int, default=128000,
                      help='Audio bitrate in bps (default: 128000)')
    parser.add_argument('--format', type=str, default='mp3',
                      choices=['mp3', 'pcm', 'wav'],
                      help='Audio format (default: mp3)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    # Check for required environment variables
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        logger.info(f"Please set these environment variables and try again.")
        sys.exit(1)
    
    # Run the test
    success = test_tts(
        output_dir=args.output_dir,
        text=args.text,
        voice_id=args.voice_id,
        speed=args.speed,
        vol=args.vol,
        pitch=args.pitch,
        audio_sample_rate=args.audio_sample_rate,
        bitrate=args.bitrate,
        format=args.format
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
