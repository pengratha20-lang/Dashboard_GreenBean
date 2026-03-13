// Green Bean - Enhanced Index Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    // ============ Navbar Scroll Effect ============
    const navbar = document.getElementById('main-navbar');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // ============ Smooth Scrolling for Internal Links ============
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // ============ Search Functionality ============
    const searchInput = document.querySelector('.search-container input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const searchTerm = this.value.trim();
                if (searchTerm) {
                    // Redirect to product page with search parameter
                    window.location.href = `product.html?search=${encodeURIComponent(searchTerm)}`;
                }
            }
        });
        
        const searchButton = document.querySelector('.search-container button');
        if (searchButton) {
            searchButton.addEventListener('click', function() {
                const searchTerm = searchInput.value.trim();
                if (searchTerm) {
                    window.location.href = `product.html?search=${encodeURIComponent(searchTerm)}`;
                }
            });
        }
    }
    
    // ============ Newsletter Subscription ============
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('input[type="email"]').value;
            
            // Simulate newsletter subscription
            if (email) {
                // Show success message
                showToast('Thank you for subscribing to our newsletter!', 'success');
                this.reset();
            }
        });
    }
    
    // ============ Animation on Scroll ============
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.feature-card, .category-card, .product-card, .care-card, .testimonial-card, .service-card').forEach(el => {
        observer.observe(el);
    });
    
    // ============ Counter Animation for Statistics ============
    const statsSection = document.querySelector('.stats-section');
    if (statsSection) {
        const statsObserver = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounters();
                    statsObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        statsObserver.observe(statsSection);
    }
    
    function animateCounters() {
        const counters = document.querySelectorAll('.stat-item h3');
        counters.forEach(counter => {
            const target = parseInt(counter.textContent.replace(/[^\d]/g, ''));
            const suffix = counter.textContent.replace(/[\d]/g, '');
            let current = 0;
            const increment = target / 50;
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    counter.textContent = target + suffix;
                    clearInterval(timer);
                } else {
                    counter.textContent = Math.floor(current) + suffix;
                }
            }, 30);
        });
    }
    
    // ============ Toast Notification System ============
    function showToast(message, type = 'success') {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.custom-toast');
        existingToasts.forEach(toast => toast.remove());
        
        // Create toast
        const toast = document.createElement('div');
        toast.className = `custom-toast alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed`;
        toast.style.cssText = `
            top: 100px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
    
    // ============ Cart Badge Update ============
    function updateCartBadge() {
        const cartBadge = document.getElementById('cart-badge');
        if (cartBadge) {
            // Get cart from localStorage (same key as shop.js)
            let cart = JSON.parse(localStorage.getItem('cart')) || [];
            
            // Optional: Clear cart if it's older than 24 hours (uncomment to enable)
            // const cartTimestamp = localStorage.getItem('cart_timestamp');
            // const now = Date.now();
            // if (cartTimestamp && (now - parseInt(cartTimestamp)) > 24 * 60 * 60 * 1000) {
            //     localStorage.removeItem('cart');
            //     localStorage.removeItem('cart_timestamp');
            //     cart = [];
            // }
            
            const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
            cartBadge.textContent = totalItems;
            
            // Add visual feedback if cart has items
            if (totalItems > 0) {
                cartBadge.style.display = 'inline';
                cartBadge.parentElement.classList.add('has-items');
            } else {
                cartBadge.style.display = 'inline';
                cartBadge.parentElement.classList.remove('has-items');
            }
        }
    }
    
    // Initialize cart badge
    updateCartBadge();
    
    // Listen for storage changes to update cart badge when cart is modified on other pages
    window.addEventListener('storage', function(e) {
        if (e.key === 'cart') {
            updateCartBadge();
        }
    });
    
    // Also listen for custom cart update events
    window.addEventListener('cartUpdated', updateCartBadge);
    
    // Periodically check for cart updates (fallback)
    setInterval(updateCartBadge, 1000);
    
    // Add a debug function to clear cart (for testing)
    window.clearCartDebug = function() {
        localStorage.removeItem('cart');
        updateCartBadge();
        console.log('Cart cleared for testing');
        showToast('Cart cleared!', 'success');
    };
    
    // ============ Mobile Menu Enhancements ============
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navbarCollapse.contains(e.target) && !navbarToggler.contains(e.target)) {
                const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                if (bsCollapse && navbarCollapse.classList.contains('show')) {
                    bsCollapse.hide();
                }
            }
        });
        
        // Close mobile menu when clicking on links
        navbarCollapse.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) {
                    const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsCollapse) {
                        bsCollapse.hide();
                    }
                }
            });
        });
    }
    
    // ============ Carousel Auto-pause on Hover ============
    const heroCarousel = document.getElementById('heroCarousel');
    if (heroCarousel) {
        heroCarousel.addEventListener('mouseenter', function() {
            bootstrap.Carousel.getInstance(this).pause();
        });
        
        heroCarousel.addEventListener('mouseleave', function() {
            bootstrap.Carousel.getInstance(this).cycle();
        });
    }
    
    // ============ Lazy Loading for Images ============
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // ============ Service Worker Registration (for PWA features) ============
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/sw.js')
                .then(function(registration) {
                    console.log('SW registered: ', registration);
                })
                .catch(function(registrationError) {
                    console.log('SW registration failed: ', registrationError);
                });
        });
    }
    
    console.log('Green Bean - Index page initialized successfully!');
});

// ============ Utility Functions ============
function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(price);
}

function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}
