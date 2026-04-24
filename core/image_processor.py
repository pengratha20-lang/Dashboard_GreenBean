"""
Image processor for generating multiple sizes (thumbnail, resized, original)
from uploaded product images.
"""

import os
from PIL import Image
from pathlib import Path
from core.image_helper import ImagePathHelper
from config.settings import IMAGE_TYPES, IMAGE_VERSIONS


class ImageProcessor:
    """
    Process images into multiple sizes:
    - Original: Keep as-is (max 2MB)
    - Resized: 400x400 for product cards
    - Thumbnail: 200x200 for product lists
    """
    
    # Image size specifications
    SIZES = {
        'resized': (400, 400),      # Card size
        'thumbnail': (200, 200),    # List size
    }
    
    @staticmethod
    def process_image(source_path, image_type='product', filename=None):
        """
        Process an image into different sizes.
        
        Args:
            source_path (str): Path to source image file
            image_type (str): Type of image ('product', 'user', 'category')
            filename (str): Output filename (uses source filename if not provided)
            
        Returns:
            dict: Status with results for each version
        """
        if not os.path.exists(source_path):
            return {'success': False, 'error': 'Source file not found'}
        
        filename = filename or os.path.basename(source_path)
        results = {}
        
        try:
            # Open and validate source image
            img = Image.open(source_path)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Convert RGBA to RGB
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Ensure folders exist
            ImagePathHelper.ensure_folders_exist(image_type)
            
            # Save original (resized to max dimensions but keep aspect ratio)
            max_size = 1024
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            original_path = ImagePathHelper.get_file_path(image_type, filename, 'original')
            img.save(original_path, 'JPEG', quality=90, optimize=True)
            results['original'] = 'success'
            
            # Generate resized versions
            for version, size in ImageProcessor.SIZES.items():
                version_img = img.copy()
                version_img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Create new image with size and paste
                new_img = Image.new('RGB', size, (240, 240, 240))
                offset = ((size[0] - version_img.width) // 2,
                         (size[1] - version_img.height) // 2)
                new_img.paste(version_img, offset)
                
                # Save version
                version_path = ImagePathHelper.get_file_path(image_type, filename, version)
                new_img.save(version_path, 'JPEG', quality=85, optimize=True)
                results[version] = 'success'
            
            return {'success': True, 'filename': filename, 'results': results}
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': results
            }
    
    @staticmethod
    def process_directory(source_dir, image_type='product', delete_source=False):
        """
        Batch process all images in a directory.
        
        Args:
            source_dir (str): Directory containing images
            image_type (str): Type of image
            delete_source (bool): Delete source files after processing
            
        Returns:
            dict: Processing results for all files
        """
        if not os.path.isdir(source_dir):
            return {'success': False, 'error': 'Source directory not found'}
        
        results = {}
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        try:
            for filename in os.listdir(source_dir):
                file_path = os.path.join(source_dir, filename)
                
                if os.path.isfile(file_path) and os.path.splitext(filename)[1].lower() in valid_extensions:
                    result = ImageProcessor.process_image(file_path, image_type, filename)
                    results[filename] = result
                    
                    if delete_source and result.get('success'):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            results[filename]['delete_error'] = str(e)
            
            return {'success': True, 'processed': len(results), 'results': results}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_placeholder_image(image_type='product', filename='placeholder.jpg', text='No Image'):
        """
        Create a placeholder image when actual image is missing.
        
        Args:
            image_type (str): Type of image
            filename (str): Filename for placeholder
            text (str): Text to display
            
        Returns:
            dict: Status of placeholder creation
        """
        results = {}
        
        try:
            ImagePathHelper.ensure_folders_exist(image_type)
            
            # Create placeholders for each size
            sizes = {
                'original': (800, 600),
                'resized': (400, 400),
                'thumbnail': (200, 200),
            }
            
            for version, (width, height) in sizes.items():
                img = Image.new('RGB', (width, height), (220, 220, 220))
                
                # Add text if PIL has ImageDraw
                try:
                    from PIL import ImageDraw, ImageFont
                    draw = ImageDraw.Draw(img)
                    
                    # Try to use default font
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
                    
                    # Calculate text position
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    x = (width - text_width) // 2
                    y = (height - text_height) // 2
                    
                    draw.text((x, y), text, fill=(100, 100, 100), font=font)
                except:
                    pass
                
                # Save placeholder
                placeholder_path = ImagePathHelper.get_file_path(image_type, filename, version)
                img.save(placeholder_path, 'JPEG', quality=85)
                results[version] = 'created'
            
            return {'success': True, 'filename': filename, 'results': results}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Convenience function for templates
def get_product_image_urls(image_filename):
    """
    Get all image URLs for a product.
    Returns URLs even if images don't exist yet (for fallback handling).
    """
    return {
        'thumbnail': ImagePathHelper.get_url_path('product', image_filename, 'thumbnail'),
        'card': ImagePathHelper.get_url_path('product', image_filename, 'resized'),
        'original': ImagePathHelper.get_url_path('product', image_filename, 'original'),
    }
