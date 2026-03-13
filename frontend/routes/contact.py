from flask import Blueprint, render_template, request, jsonify, flash
from services.telegram_bot import send_telegram_alert
import re

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle form submission
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            message = request.form.get('message', '').strip()
            
            # Validate form data
            if not name or not email or not message:
                return jsonify({
                    'success': False, 
                    'message': 'All fields are required!'
                }), 400
            
            # Validate email format
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({
                    'success': False,
                    'message': 'Please enter a valid email address!'
                }), 400
            
            # Format message for Telegram
            telegram_message = f"""
🌱 <b>New Contact Form Submission</b> 🌱

👤 <b>Name:</b> {name}
📧 <b>Email:</b> {email}

💬 <b>Message:</b>
{message}

⏰ <b>Received at:</b> {request.environ.get('HTTP_HOST', 'Unknown')}
"""
            
            # Send to Telegram
            success = send_telegram_alert(telegram_message)
            
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
    
    # GET request - show the contact form
    return render_template('home/contact.html', title="Green Garden - Contact Us")
