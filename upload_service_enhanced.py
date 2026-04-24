"""
Enhanced Upload Service with Organized Image Structure

Supports both:
1. Legacy: save_image(file, upload_folder, ...) - for backward compatibility
2. Modern: save_image_organized(file, image_type, ...) - for new organized structure

Gradually migrate your code from legacy to modern method.
"""

import os
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from core.image_helper import ImagePathHelper


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return (
            '.' in filename and
            filename.rsplit('.', 1)[1].lower() in allowed_extensions
    )


def add_watermark(image, watermark_text="© Dashboard"):
    """Add a watermark text to the image"""
    try:
        img_with_watermark = image.copy()
        draw = ImageDraw.Draw(img_with_watermark, 'RGBA')

        img_width, img_height = img_with_watermark.size

        try:
            font_size = int(img_height / 15)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = 10
        x = img_width - text_width - padding
        y = img_height - text_height - padding

        draw.text((x, y), watermark_text, font=font, fill=(100, 100, 100, 200))
        
        return img_with_watermark
    except Exception as e:
        print(f"Warning: Could not add watermark: {e}")
        return image


def save_image(
        file,
        upload_folder,
        allowed_extensions,
        resize_to=(400, 400),
        thumb_size=(200, 200),
        watermark_text="© GreenBean"
):
    """
    LEGACY METHOD - Use save_image_organized() for new projects
    
    Saves image to a flat folder structure (backward compatible)
    Creates: original, resized_, thumb_ versions
    """
    if not file or file.filename == '':
        return 'no file'

    if not allowed_file(file.filename, allowed_extensions):
        return 'invalid file'

    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
    filename_with_timestamp = timestamp + filename
    name_with_timestamp = timestamp + name

    original_path = os.path.join(upload_folder, filename_with_timestamp)
    resized_path = os.path.join(upload_folder, f"resized_{name_with_timestamp}{ext}")
    thumb_path = os.path.join(upload_folder, f"thumb_{name_with_timestamp}{ext}")

    file.save(original_path)

    image = Image.open(original_path)
    img_with_watermark = add_watermark(image, watermark_text)
    img_with_watermark.save(original_path)

    resized = image.copy()
    resized.thumbnail(resize_to)
    resized_with_watermark = add_watermark(resized, watermark_text)
    resized_with_watermark.save(resized_path)

    thumb = image.copy()
    thumb.thumbnail(thumb_size)
    thumb_with_watermark = add_watermark(thumb, watermark_text)
    thumb_with_watermark.save(thumb_path)

    return {
        "original": filename_with_timestamp,
        "resized": f"resized_{name_with_timestamp}{ext}",
        "thumbnail": f"thumb_{name_with_timestamp}{ext}"
    }


def save_image_organized(
        file,
        image_type='other',
        resize_to=(400, 400),
        thumb_size=(200, 200),
        watermark_text="© GreenBean"
):
    """
    MODERN METHOD - Recommended for new code
    
    Saves image to organized folder structure:
    - static/images/{image_type}/original/
    - static/images/{image_type}/resized/
    - static/images/{image_type}/thumbnails/
    
    Args:
        file: File object from request.files
        image_type: Type of image ('product', 'user', 'category', 'other')
        resize_to: Tuple for resized image dimensions (default: 400x400)
        thumb_size: Tuple for thumbnail dimensions (default: 200x200)
        watermark_text: Text to add as watermark
        
    Returns:
        dict: Filenames of saved images, or error string
        
    Example:
        result = save_image_organized(
            file=request.files['image'],
            image_type='product',
            watermark_text='© GreenBean'
        )
        if isinstance(result, dict):
            product.image = result['original']  # Store just the filename
    """
    if not file or file.filename == '':
        return 'no file'

    from config.settings import ALLOWED_EXTENSIONS
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        return 'invalid file'

    try:
        # Ensure folders exist
        ImagePathHelper.ensure_folders_exist(image_type)
        
        # Prepare filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename_with_timestamp = timestamp + filename
        name_with_timestamp = timestamp + name
        
        # Save original
        original_path = ImagePathHelper.get_file_path(
            image_type, filename_with_timestamp, 'original'
        )
        file.save(original_path)
        
        # Load image and add watermark
        image = Image.open(original_path)
        img_with_watermark = add_watermark(image, watermark_text)
        img_with_watermark.save(original_path)
        
        # Create and save resized version
        resized_filename = f"resized_{name_with_timestamp}{ext}"
        resized_path = ImagePathHelper.get_file_path(
            image_type, resized_filename, 'resized'
        )
        resized = image.copy()
        resized.thumbnail(resize_to)
        resized_with_watermark = add_watermark(resized, watermark_text)
        resized_with_watermark.save(resized_path)
        
        # Create and save thumbnail version
        thumb_filename = f"thumb_{name_with_timestamp}{ext}"
        thumb_path = ImagePathHelper.get_file_path(
            image_type, thumb_filename, 'thumbnail'
        )
        thumb = image.copy()
        thumb.thumbnail(thumb_size)
        thumb_with_watermark = add_watermark(thumb, watermark_text)
        thumb_with_watermark.save(thumb_path)
        
        return {
            'original': filename_with_timestamp,
            'resized': resized_filename,
            'thumbnail': thumb_filename
        }
        
    except Exception as e:
        print(f"Error saving image: {e}")
        return f'error: {str(e)}'


def delete_image_organized(image_type, filename):
    """
    Delete all versions of an image using the organized structure.
    
    Args:
        image_type: Type of image ('product', 'user', 'category', 'other')
        filename: Filename of the image
        
    Returns:
        dict: Status of deletion for each version
        
    Example:
        result = delete_image_organized('product', 'image.jpg')
        # Returns: {'original': 'deleted', 'resized': 'deleted', 'thumbnail': 'deleted'}
    """
    return ImagePathHelper.delete_all_versions(image_type, filename)


def get_image_url(filename, image_type='product', version='resized'):
    """
    Get the URL path for displaying an image in templates.
    
    Args:
        filename: Filename of the image
        image_type: Type of image ('product', 'user', 'category', 'other')
        version: Version of image ('original', 'resized', 'thumbnail')
        
    Returns:
        str: URL path for the image
        
    Example:
        url = get_image_url('20260128_213448_artificial_plants.jpg', 'product', 'resized')
        # Returns: /static/images/product/resized/20260128_213448_artificial_plants.jpg
    """
    return ImagePathHelper.get_url_path(image_type, filename, version)


def get_image_path(filename, image_type='product', version='original'):
    """
    Get the file system path for an image.
    
    Args:
        filename: Filename of the image
        image_type: Type of image ('product', 'user', 'category', 'other')
        version: Version of image ('original', 'resized', 'thumbnail')
        
    Returns:
        str: Absolute file path
        
    Example:
        path = get_image_path('20260128_213448_artificial_plants.jpg', 'product')
        # Returns: C:\\path\\to\\Dashboard_Project\\static\\images\\product\\original\\...
    """
    return ImagePathHelper.get_file_path(image_type, filename, version)
