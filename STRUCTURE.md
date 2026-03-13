# GreenBean Dashboard Project - Reorganized Structure

## 📁 Project Structure Overview

After reorganization, the project now uses a unified folder structure that clearly separates frontend and backend while sharing common modules:

```
Dashboard_Project/
│
├── 📂 templates/main/
│   ├── dashboard/          # Admin Dashboard Templates
│   │   ├── analytics.html
│   │   ├── login.html
│   │   ├── products.html
│   │   ├── orders.html
│   │   ├── customers.html
│   │   ├── discounts.html
│   │   ├── register.html
│   │   ├── settings.html
│   │   ├── user.html
│   │   ├── components/
│   │   │   ├── topbar.html
│   │   │   ├── sidebar.html
│   │   │   └── footer.html
│   │   └── users_action/
│   │       ├── add_user.html
│   │       └── edit_user.html
│   │
│   └── frontside/          # Customer Website Templates
│       ├── base.html
│       ├── auth-base.html
│       ├── shop-base.html
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── checkout/
│       │   └── checkout.html
│       ├── home/
│       │   └── index.html
│       ├── shop/
│       │   └── all_product.html
│       └── components/
│           ├── shop-navbar.html
│           └── footer.html
│
├── 📂 routes/main/
│   ├── dashboard/          # Admin Routes
│   │   ├── auth.py         # Admin authentication
│   │   ├── dashboard.py    # Dashboard overview
│   │   ├── product.py      # Product management
│   │   ├── order.py        # Order management
│   │   ├── customer.py     # Customer management
│   │   ├── category.py     # Category management
│   │   ├── discount.py     # Discount management
│   │   ├── analytics.py    # Analytics & reports
│   │   ├── setting.py      # Settings management
│   │   ├── user.py         # User management
│   │   ├── product_api.py  # Product API endpoints
│   │   └── __init__.py
│   │
│   └── frontside/          # Customer Routes
│       ├── index.py        # Home page
│       ├── about.py        # About page
│       ├── contact.py      # Contact page
│       ├── service.py      # Services page
│       ├── shop.py         # Shop/Products page
│       ├── cart.py         # Shopping cart
│       ├── product.py      # Product details
│       ├── checkout.py     # Checkout process
│       ├── auth.py         # Customer login/register
│       ├── wishlist_routes.py  # Wishlist management
│       ├── orders_routes.py    # Customer orders
│       ├── discount.py     # Discount handling
│       └── __init__.py
│
├── 📂 static/main/
│   ├── dashboard/          # Admin Assets
│   │   └── (admin CSS, JS, images)
│   │
│   └── frontside/          # Customer Assets
│       ├── css/
│       │   └── styles.css
│       ├── js/
│       │   ├── common.js
│       │   ├── dashboard.js
│       │   └── charts-utils.js
│       ├── images/
│       │   ├── category/
│       │   ├── product/
│       │   ├── user/
│       │   └── uploads/
│       └── upload/
│
├── 📂 services/main/
│   ├── dashboard/          # Admin Services
│   │   ├── coupons.py      # Coupon logic
│   │   └── __init__.py
│   │
│   └── frontside/          # Customer Services
│       ├── coupons.py      # Coupon validation
│       ├── telegram_bot.py # Telegram notifications
│       └── __init__.py
│
├── 📂 model/               # Shared Data Models
│   ├── __init__.py
│   ├── user.py            # Admin users
│   ├── customer.py        # Customers
│   ├── product.py         # Products
│   ├── category.py        # Categories
│   ├── order.py           # Orders
│   ├── order_item.py      # Order items
│   ├── discount.py        # Discounts
│   ├── wishlist.py        # Customer wishlist
│   └── setting.py         # Settings
│
├── 📂 migrations/          # Database Migrations
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── 📄 app_unified.py       # Main Unified Application (reads APP_MODE env var)
├── 📄 run_frontend.py      # Frontend Launcher (port 5000)
├── 📄 run_backend.py       # Backend Launcher (port 5001)
├── 📄 app.py               # Legacy app (if needed)
│
├── 📄 database.py          # Database configuration
├── 📄 config.py            # App configuration
├── 📄 auth_helper.py       # Authentication utilities
├── 📄 image_helper.py      # Image processing
├── 📄 upload_service_enhanced.py  # File upload service
├── 📄 init_db.py           # Database initialization
├── 📄 init_database.py     # Sample data initialization
│
├── 📄 requirement.txt       # Python dependencies
├── 📄 README.md            # Project readme
└── 📄 .gitignore           # Git ignore file
```

---

## 🚀 Running the Application

### Frontend (Customer Website)
**Port: 5000**

```bash
python run_frontend.py
```

**Access at:** http://localhost:5000

**Features:**
- Customer home page
- Product browse & search
- Shopping cart
- Checkout
- Customer login/register
- User wishlist
- Order history
- Contact form

---

### Backend (Admin Dashboard)
**Port: 5001**

```bash
python run_backend.py
```

**Access at:** http://localhost:5001

**Features:**
- Admin authentication
- Dashboard overview
- Product management
- Order management
- Customer management
- Category management
- Discount management
- Analytics & reports
- User management
- Settings

---

## 🔐 Default Credentials

### Admin Login
```
Username: admin
Password: admin123
URL: http://localhost:5001/login
```

### Sample Customer
```
Email: customer@example.com
URL: http://localhost:5000
```

---

## 📦 Environment Setup

### Install Dependencies
```bash
pip install -r requirement.txt
```

### Create & Initialize Database
```bash
python init_database.py
```

### Run Using Environment Variables
```bash
# Frontend
set APP_MODE=frontend && python app_unified.py

# Backend
set APP_MODE=backend && python app_unified.py
```

---

## 📝 Key Files Modified

1. **app_unified.py** - Main application that handles both frontend and backend
2. **run_frontend.py** - Frontend launcher script
3. **run_backend.py** - Backend launcher script
4. **routes/** - Reorganized with main/dashboard and main/frontside
5. **templates/** - Reorganized with main/dashboard and main/frontside
6. **static/** - Reorganized with main/dashboard and main/frontside
7. **services/** - Reorganized with main/dashboard and main/frontside

---

## 🔄 Import Path Changes

### Old Structure (before reorganization)
```python
from frontend.routes.shop import shop_bp
from backend.routes.admin.product import product_bp
from frontend.services.coupons import validate_coupon
from backend.services.coupons import increment_usage
```

### New Structure (after reorganization)
```python
from routes.main.frontside.shop import shop_bp
from routes.main.dashboard.product import product_bp
from services.main.frontside.coupons import validate_coupon
from services.main.dashboard.coupons import increment_usage
```

---

## 🧪 Testing the Applications

### Test Frontend Routes
```
GET http://localhost:5000/        → Home (redirects)
GET http://localhost:5000/home    → Customer home page
GET http://localhost:5000/shop    → Product listing
GET http://localhost:5000/contact → Contact form
GET http://localhost:5000/about   → About page
```

### Test Backend Routes
```
GET http://localhost:5001/        → Dashboard (redirects to login)
GET http://localhost:5001/login   → Admin login form
GET http://localhost:5001/dashboard → Admin dashboard (requires authentication)
GET http://localhost:5001/products  → Product management
GET http://localhost:5001/orders    → Order management
```

---

## 📚 Database Schema

Shared models used by both frontend and backend:

- **User** - Admin users
- **Customer** - Customer accounts
- **Product** - Products in catalog
- **Category** - Product categories
- **Order** - Customer orders
- **OrderItem** - Items in orders
- **Discount** - Discount/coupon codes
- **Wishlist** - Customer wishlists
- **Setting** - Application settings

---

## 🎯 Next Steps

1. ✅ Reorganized project structure
2. ✅ Separated frontend (port 5000) and backend (port 5001)
3. ✅ Created unified app with APP_MODE support
4. ✅ Fixed all import paths
5. ⏭️ Test both applications thoroughly
6. ⏭️ Deploy to production
7. ⏭️ Set up CI/CD pipeline

---

**Last Updated:** March 13, 2026
**Status:** ✅ Structure Reorganization Complete
