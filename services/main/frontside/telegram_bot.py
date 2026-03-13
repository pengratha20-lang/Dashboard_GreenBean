import requests

def send_telegram_alert(message):
    try:
        bot_token = "7980568529:AAE8nIaaMhPStyv6aV-rFU4KTVs9P9Jn8k0"
        chat_id = "1081886446"
        
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