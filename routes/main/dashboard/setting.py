from flask import render_template, request, jsonify, Blueprint
from core.database import db
from core.auth_helper import login_required
from model.setting import Setting

# Create Blueprint
settings_bp = Blueprint('settings_module', __name__, url_prefix='')

@settings_bp.route('/settings')
@login_required
def settings_route():
    setting = Setting.query.first()
    if not setting:
        # Create default settings if none exist
        setting = Setting(
            store_name='Green Bean',
            store_email='admin@greenbean.local',
            store_phone='',
            store_address='Phnom Penh',
            store_city='Phnom Penh',
            store_country='Cambodia',
            currency='USD',
            default_currency='USD',
            language='en',
            timezone='Asia/Phnom_Penh',
            tax_rate=0,
            shipping_cost=2.5,
            exchange_rate_usd_to_khr=4100
        )
        db.session.add(setting)
        db.session.commit()
    
    settings_data = setting.to_dict() if setting else {}
    return render_template('dashboard/settings.html', setting=settings_data, module_name='Settings', module_icon='fa-cog')

@settings_bp.route('/settings/update', methods=['POST'])
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
        setting.default_currency = data.get('default_currency', setting.default_currency)
        setting.language = data.get('language', setting.language)
        setting.timezone = data.get('timezone', setting.timezone)
        
        tax_rate = data.get('tax_rate')
        if tax_rate is not None:
            setting.tax_rate = float(tax_rate)
            
        shipping_cost = data.get('shipping_cost')
        if shipping_cost is not None:
            setting.shipping_cost = float(shipping_cost)

        exchange_rate = data.get('exchange_rate_usd_to_khr')
        if exchange_rate is not None:
            setting.exchange_rate_usd_to_khr = float(exchange_rate)
             
        setting.logo_url = data.get('logo_url', setting.logo_url)
        
        db.session.add(setting)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Settings updated successfully', 'data': setting.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
