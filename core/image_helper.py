import os
from config.settings import IMAGE_TYPES, IMAGE_VERSIONS


class ImagePathHelper:
    """
    Centralized image path management for organized image storage.
    
    Usage:
        # Get paths for backend file operations
        original_path = ImagePathHelper.get_file_path('product', 'image.jpg', 'original')
        
        # Get URLs for frontend templates
        url = ImagePathHelper.get_url_path('product', 'image.jpg', 'resized')
        
        # Ensure folders exist before saving
        ImagePathHelper.ensure_folders_exist('product')
    """
    
    @staticmethod
    def get_folder_for_type(image_type, version='original'):
        """
        Get the absolute folder path for specific image type and version.
        
        Args:
            image_type (str): Type of image ('product', 'user', 'category', 'other')
            version (str): Version type ('original', 'resized', 'thumbnail')
            
        Returns:
            str: Absolute path to the folder
        """
        base_path = IMAGE_TYPES.get(image_type, IMAGE_TYPES['other'])
        version_folder = IMAGE_VERSIONS.get(version, 'original')
        return os.path.join(base_path, version_folder)
    
    @staticmethod
    def get_url_path(image_type, filename, version='original'):
        """
        Get the URL path for frontend to use in templates/API.
        Perfect for Flask's url_for() or direct HTML img src.
        
        Example:
            url = ImagePathHelper.get_url_path('product', 'img.jpg', 'resized')
            # Returns: /static/images/product/resized/img.jpg
            
        Args:
            image_type (str): Type of image
            filename (str): Name of the file
            version (str): Version type
            
        Returns:
            str: URL path relative to domain
        """
        version_folder = IMAGE_VERSIONS.get(version, 'original')
        return f"/static/images/{image_type}/{version_folder}/{filename}"
    
    @staticmethod
    def get_file_path(image_type, filename, version='original'):
        """
        Get the absolute file path for backend file operations (read/write/delete).
        
        Example:
            path = ImagePathHelper.get_file_path('product', 'img.jpg', 'original')
            # Returns: C:\\path\\to\\static\\images\\product\\original\\img.jpg
            
        Args:
            image_type (str): Type of image
            filename (str): Name of the file
            version (str): Version type
            
        Returns:
            str: Absolute file path
        """
        return os.path.join(
            ImagePathHelper.get_folder_for_type(image_type, version),
            filename
        )
    
    @staticmethod
    def ensure_folders_exist(image_type):
        """
        Ensure all version folders exist for an image type.
        Call this before saving images of a specific type.
        
        Args:
            image_type (str): Type of image
        """
        for version in IMAGE_VERSIONS.values():
            folder = ImagePathHelper.get_folder_for_type(image_type, version)
            os.makedirs(folder, exist_ok=True)
    
    @staticmethod
    def delete_all_versions(image_type, filename):
        """
        Delete all versions of an image (original, resized, thumbnail).
        Useful for cleanup when removing products or users.
        
        Args:
            image_type (str): Type of image
            filename (str): Name of the file
            
        Returns:
            dict: Status of each deletion attempt
        """
        results = {}
        for version in IMAGE_VERSIONS.values():
            file_path = ImagePathHelper.get_file_path(image_type, filename, version)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    results[version] = 'deleted'
                else:
                    results[version] = 'not_found'
            except Exception as e:
                results[version] = f'error: {str(e)}'
        return results
    
    @staticmethod
    def get_image_size_info(image_type, filename, version='original'):
        """
        Get size information about an image file.
        
        Args:
            image_type (str): Type of image
            filename (str): Name of the file
            version (str): Version type
            
        Returns:
            dict: File size information (size_bytes, size_kb, size_mb)
        """
        file_path = ImagePathHelper.get_file_path(image_type, filename, version)
        
        if not os.path.exists(file_path):
            return {'exists': False}
        
        size_bytes = os.path.getsize(file_path)
        return {
            'exists': True,
            'size_bytes': size_bytes,
            'size_kb': round(size_bytes / 1024, 2),
            'size_mb': round(size_bytes / (1024 * 1024), 2)
        }
    
    @staticmethod
    def list_images_of_type(image_type, version='original'):
        """
        List all images of a specific type and version.
        Useful for admin panels or cleanup scripts.
        
        Args:
            image_type (str): Type of image
            version (str): Version type
            
        Returns:
            list: List of filenames in that folder
        """
        folder = ImagePathHelper.get_folder_for_type(image_type, version)
        if os.path.exists(folder):
            return os.listdir(folder)
        return []
    
    @staticmethod
    def get_all_image_types():
        """
        Get all configured image types.
        
        Returns:
            list: List of available image types
        """
        return list(IMAGE_TYPES.keys())
    
    @staticmethod
    def get_all_versions():
        """
        Get all configured image versions.
        
        Returns:
            list: List of available versions
        """
        return list(IMAGE_VERSIONS.values())


# Convenience functions for quick access
def get_image_url(filename, image_type='product', version='resized'):
    """Quick shortcut for templates: {{ get_image_url('img.jpg', 'product') }}"""
    return ImagePathHelper.get_url_path(image_type, filename, version)


def get_image_path(filename, image_type='product', version='original'):
    """Quick shortcut for backend: get_image_path('img.jpg', 'product')"""
    return ImagePathHelper.get_file_path(image_type, filename, version)
