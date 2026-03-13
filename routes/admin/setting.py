from flask import render_template, request, jsonify, Blueprint
from database import db
from auth_helper import login_required
from model.setting import Setting

# Create Blueprint
admin_bp = Blueprint('settings_module', __name__, url_prefix='')

@admin_bp.route('/settings')
@login_required
def settings_route():
    setting = Setting.query.first()
    if not setting:
        # Create default settings if none exist
        setting = Setting(
            store_name='Green Bean Admin',
            store_email='admin@greenbean.com',
            store_phone='+1 (555) 123-4567',
            store_address='123 Plant Street',
            store_city='Garden City',
            store_country='USA'
        )
        db.session.add(setting)
        db.session.commit()
    
    settings_data = setting.to_dict() if setting else {}
    return render_template('dashboard/settings.html', setting=settings_data, module_name='Settings', module_icon='fa-cog')

@admin_bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    try:
        setting = Setting.query.first()
        if not setting:
            setting = Setting()
        
        data = request.form
        
        setting.store_name = data.get('store_name', setting.store_name)
        setting.store_email = data.get('store_email', setting.store_email)
        setting.store_phone = data.get('store_phone', setting.store_phone)
        setting.store_address = data.get('store_address', setting.store_address)
        setting.store_city = data.get('store_city', setting.store_city)
        setting.store_country = data.get('store_country', setting.store_country)
        setting.currency = data.get('currency', setting.currency)
        setting.language = data.get('language', setting.language)
        setting.timezone = data.get('timezone', setting.timezone)
        setting.tax_rate = float(data.get('tax_rate', setting.tax_rate))
        setting.shipping_cost = float(data.get('shipping_cost', setting.shipping_cost))
        setting.logo_url = data.get('logo_url', setting.logo_url)
        
        db.session.add(setting)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Settings updated successfully', 'data': setting.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
