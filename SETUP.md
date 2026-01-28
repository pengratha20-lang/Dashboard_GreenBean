# GreenBean E-commerce Dashboard - Setup Guide

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/pengratha20-lang/GreenBean_Ecommerce.git
cd GreenBean_Ecommerce
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirement.txt
```

### 4. Initialize Database
```bash
python init_db.py
```

This will create a fresh SQLite database with:
- All required tables
- A default admin account (username: `admin`, password: `admin123`)
- Sample categories for testing

**⚠️ Important:** Change the default admin password immediately after first login!

### 5. Run the Application
```bash
# Using the batch script (Windows)
run.bat

# OR using Python directly
python app.py
```

The application will be available at `http://localhost:5000`

## Default Login Credentials
- **Username:** admin
- **Email:** admin@greenbeans.com
- **Password:** admin123

⚠️ Change these credentials immediately in production!

## Project Structure
```
├── app.py                 # Main Flask application
├── database.py           # Database configuration
├── config.py             # Application configuration
├── model/                # Database models
├── routes/               # API routes and blueprints
├── templates/            # HTML templates
├── static/               # CSS, JS, images, uploads
├── migrations/           # Alembic database migrations
├── init_db.py           # Database initialization script
└── requirement.txt       # Python dependencies
```

## Troubleshooting

### "No module named 'flask'"
Make sure you've installed all dependencies:
```bash
pip install -r requirement.txt
```

### Database errors
If you encounter database errors, reinitialize:
```bash
python init_db.py
```
When prompted, enter `yes` to reinitialize the database.

### Port already in use
If port 5000 is already in use, edit `app.py` and change the port number in the `app.run()` call.

## Support
For issues or questions, please open an issue on GitHub.
