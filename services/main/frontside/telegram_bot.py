import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_telegram_alert(message):
    try:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        # Skip if credentials not configured
        if not bot_token or not chat_id:
            print("⚠️  Telegram credentials not configured. Skipping notification.")
            return False
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        print(f"Sending to Telegram: {url}")
        print(f"Message: {message}")
        
        response = requests.post(url, data=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Telegram error: {e}")
        return False