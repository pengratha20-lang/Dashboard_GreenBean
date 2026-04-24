"""
Telegram Notifier Service for Payment Alerts
Sends real-time notifications to admin when customer payments are received
"""

import os
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send payment notifications via Telegram bot"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.admin_id = os.getenv('TELEGRAM_ADMIN_USER_ID', '')
        self.enabled = os.getenv('TELEGRAM_ENABLE_NOTIFICATIONS', 'False').lower() == 'true'
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        print(f'\n📱 Telegram Service Initialized:')
        print(f'   Token Available: {bool(self.token)}')
        print(f'   Admin ID: {self.admin_id}')
        print(f'   Enabled: {self.enabled}')
        
        # Validate configuration
        if not self.token or not self.admin_id:
            self.enabled = False
            print(f'   ❌ Telegram not properly configured')
            logger.warning("Telegram notifier not configured (missing token or user ID)")
        else:
            print(f'   ✅ Telegram configuration valid')
    
    def send_payment_success(self, order_id, customer_name, amount, currency, order_number='N/A'):
        """Send payment success notification to admin"""
        print(f'   🔔 Telegram Service - send_payment_success called')
        print(f'      Enabled: {self.enabled}')
        print(f'      Token: {bool(self.token)}')
        print(f'      Admin ID: {self.admin_id}')
        
        if not self.enabled:
            print(f'   ⚠️ Telegram notifications disabled')
            return False
        
        try:
            message = f"""
<b>🎉 Payment Received!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>Order Number:</b> #{order_number}
<b>Order ID:</b> {order_id}
<b>Customer Name:</b> {customer_name}
<b>Amount:</b> {amount} {currency}
<b>Status:</b> ✅ <b>PAID</b>
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            print(f'   📱 Sending message to Telegram...')
            result = self._send_message(message)
            print(f'   ✅ Send result: {result}')
            return result
        except Exception as e:
            print(f'   ❌ Exception in send_payment_success: {str(e)}')
            logger.error(f"Failed to send payment success notification: {str(e)}")
            return False
    
    def send_payment_failed(self, order_id, customer_name, amount, reason='Unknown'):
        """Send payment failure alert to admin"""
        if not self.enabled:
            return False
        
        try:
            message = f"""
<b>⚠️ Payment Failed!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>Order ID:</b> {order_id}
<b>Customer Name:</b> {customer_name}
<b>Amount:</b> {amount}
<b>Failure Reason:</b> {reason}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>Action Required:</b> Contact customer
            """
            
            return self._send_message(message)
        except Exception as e:
            logger.error(f"Failed to send payment failure notification: {str(e)}")
            return False
    
    def send_test_notification(self):
        """Send test notification to verify bot works"""
        if not self.enabled:
            return False
        
        try:
            message = f"""
<b>✅ Telegram Bot Connected!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>Bot Name:</b> Green Bean Payment Bot
<b>Status:</b> Ready to receive payment notifications
<b>Test Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your notification system is working! 🎉
            """
            
            return self._send_message(message)
        except Exception as e:
            logger.error(f"Failed to send test notification: {str(e)}")
            return False
    
    def _send_message(self, text):
        """Send message to admin via Telegram API"""
        print(f'   🔐 _send_message called')
        print(f'      Token: {bool(self.token)}')
        print(f'      Admin ID: {self.admin_id}')
        
        if not self.token or not self.admin_id:
            print(f'      ❌ Missing credentials')
            logger.warning("Telegram credentials not configured")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            print(f'   📍 URL: {url}')
            print(f'   💬 Payload chat_id: {self.admin_id}')
            
            payload = {
                'chat_id': self.admin_id,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            print(f'   🚀 Sending POST request to Telegram API...')
            response = requests.post(url, json=payload, timeout=5)
            print(f'   ✅ Response status: {response.status_code}')
            print(f'   ✅ Response text: {response.text[:200]}...')
            
            if response.ok:
                print(f'   ✅✅ Telegram message sent successfully!')
                logger.info(f"Telegram notification sent successfully")
                return True
            else:
                print(f'   ❌ Telegram API error: {response.status_code} - {response.text}')
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
        
        except requests.exceptions.Timeout:
            print(f'   ❌ Telegram API request TIMED OUT')
            logger.error("Telegram API request timed out")
            return False
        except Exception as e:
            print(f'   ❌ Exception in _send_message: {str(e)}')
            print(f'   ❌ Exception type: {type(e).__name__}')
            import traceback
            print(f'   ❌ Traceback: {traceback.format_exc()}')
            logger.error(f"Telegram send error: {str(e)}")
            return False


def get_telegram_notifier():
    """Get TelegramNotifier instance"""
    return TelegramNotifier()
