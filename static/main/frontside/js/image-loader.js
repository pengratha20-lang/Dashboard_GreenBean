/**
 * Image Loading States Handler
 * Adds skeleton loaders and handles image loading states
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add skeleton loading effect to all product images
    const images = document.querySelectorAll('img[loading="lazy"]');
    
    images.forEach(img => {
        // Add skeleton loader styling
        img.addEventListener('loadstart', function() {
            this.classList.add('image-loading');
            this.style.opacity = '0.5';
        });
        
        img.addEventListener('load', function() {
            this.classList.remove('image-loading');
            this.classList.add('image-loaded');
            this.style.opacity = '1';
        });
        
        img.addEventListener('error', function() {
            this.classList.remove('image-loading');
            this.classList.add('image-error');
            // Show default image on error
            this.src = '/static/images/default-product.png';
            this.alt = 'Image not available';
        });
    });
    
    // Also handle regular (non-lazy) images
    const allImages = document.querySelectorAll('img');
    allImages.forEach(img => {
        if (img.complete) {
            // Image already loaded
            img.classList.add('image-loaded');
        } else {
            // Trigger loading states for in-progress images
            img.addEventListener('load', function() {
                this.classList.add('image-loaded');
            });
            
            img.addEventListener('error', function() {
                this.classList.add('image-error');
                this.src = '/static/images/default-product.png';
            });
        }
    });
    
    // Handle product cards with images
    const productCards = document.querySelectorAll('.product-card img, .card img');
    productCards.forEach(img => {
        // Create placeholder while loading
        const wrapper = document.createElement('div');
        wrapper.className = 'image-wrapper position-relative';
        wrapper.style.overflow = 'hidden';
        img.parentNode.insertBefore(wrapper, img);
        wrapper.appendChild(img);
        
        // Add skeleton loader
        const skeleton = document.createElement('div');
        skeleton.className = 'image-skeleton';
        skeleton.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            z-index: 1;
        `;
        wrapper.appendChild(skeleton);
        
        img.addEventListener('load', function() {
            skeleton.style.display = 'none';
            img.style.zIndex = '2';
        });
        
        img.addEventListener('error', function() {
            skeleton.style.display = 'none';
        });
    });
});

// Add CSS for image loading animation
const style = document.createElement('style');
style.textContent = `
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    .image-loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .image-loaded {
        transition: opacity 0.3s ease-in;
        opacity: 1;
    }
    
    .image-error {
        opacity: 0.6;
        filter: grayscale(100%);
    }
    
    .image-wrapper {
        position: relative;
    }
`;
document.head.appendChild(style);
