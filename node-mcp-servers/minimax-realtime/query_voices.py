import requests
import os
import json
from dotenv import load_dotenv

# --- Instructions --- 
# 1. Make sure you have the 'python-dotenv' and 'requests' libraries installed:
#    pip install python-dotenv requests
#
# 2. Create a file named .env in the same directory as this script.
#    Add your API key to the .env file like this:
#    MINIMAX_API_KEY=your_actual_api_key_here
#
# 3. Run the script from your terminal:
#    python query_voices.py
# --------------------

# Load environment variables from .env file
load_dotenv()

api_key = os.environ.get("MINIMAX_API_KEY")

url = "https://api.minimaxi.com/v1/get_voice"

if not api_key:
    print("ERROR: API key not found.")
    print("Please create a .env file and add your MINIMAX_API_KEY to it.")
else:
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    payload = {
        'voice_type': 'all'
    }

    print("Querying available voices from MiniMax API...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        
        result = response.json()
        print("\n--- API Response ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("base_resp", {}).get("status_code") == 0:
            system_voices = result.get("system_voice", [])
            if system_voices:
                print("\n--- Available System Voices ---")
                for voice in system_voices:
                    print(f"  - Voice ID: {voice.get('voice_id')}, Name: {voice.get('voice_name')}")
            else:
                print("\nNo system voices found in the response.")
        else:
            print(f"\nAPI returned an error: {result.get('base_resp', {}).get('status_msg')}")

    except requests.exceptions.HTTPError as http_err:
        print(f"\nHTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
    except requests.exceptions.RequestException as req_err:
        print(f"\nRequest error occurred: {req_err}")
    except json.JSONDecodeError:
        print(f"\nFailed to decode JSON from response. Response content:\n{response.text}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
