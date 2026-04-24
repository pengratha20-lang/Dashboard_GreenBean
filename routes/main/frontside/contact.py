from flask import Blueprint, render_template, request, jsonify, flash
from routes.integrations.telegram_service import TelegramNotifier
import re
from datetime import datetime

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle form submission
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            message = request.form.get('message', '').strip()
            
            if not name or not email or not message:
                return jsonify({
                    'success': False, 
                    'message': 'All fields are required!'
                }), 400
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({
                    'success': False,
                    'message': 'Please enter a valid email address!'
                }), 400
            
            # Send via TelegramNotifier service (uses TELEGRAM_ADMIN_USER_ID)
            notifier = TelegramNotifier()
            
            telegram_message = f"""
🌱 <b>New Contact Form Submission</b> 🌱

👤 <b>Name:</b> {name}
📧 <b>Email:</b> {email}

💬 <b>Message:</b>
{message}

⏰ <b>Received at:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            success = notifier._send_message(telegram_message)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Thank you! Your message has been sent successfully. We\'ll get back to you soon!'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Sorry, there was an error sending your message. Please try again later.'
                }), 500
                
        except Exception as e:
            print(f"Contact form error: {e}")
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred. Please try again later.'
            }), 500
    
    return render_template('frontside/home/contact.html', title="Green Garden - Contact Us")
