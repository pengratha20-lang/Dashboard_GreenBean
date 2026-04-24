import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============= LEGACY UPLOAD FOLDER (Backward Compatibility) =============
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/upload')

# ============= NEW ORGANIZED IMAGE STRUCTURE =============
# Root folder for all organized images
IMAGES_FOLDER = os.path.join(BASE_DIR, 'static/images')

# Image type folders mapping
# Add new types here as your application grows
IMAGE_TYPES = {
    'product': os.path.join(IMAGES_FOLDER, 'product'),
    'user': os.path.join(IMAGES_FOLDER, 'user'),
    'category': os.path.join(IMAGES_FOLDER, 'category'),
    'other': os.path.join(IMAGES_FOLDER, 'uploads'),
}

# Image version folders (processing stages)
IMAGE_VERSIONS = {
    'original': 'original',      # Full resolution uploaded image
    'resized': 'resized',        # Medium size for display (400x400)
    'thumbnail': 'thumbnails',   # Small size for lists (200x200)
}

# File configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
