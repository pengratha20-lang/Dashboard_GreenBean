// Cart Badge Fix - Force Update All Cart Badges
(function() {
    'use strict';
    
    // Clear cart for guests (non-logged-in users)
    function clearGuestCart() {
        // Check if user is logged in by looking at meta tag (same as cart-sync.js)
        const userMeta = document.querySelector('meta[name="user-id"]');
        const userId = userMeta ? String(userMeta.getAttribute('content') || '').trim() : '';
        const isLoggedIn = Boolean(userId);
        
        console.log('🔍 Cart check - User ID:', userId || 'GUEST');
        
        if (!isLoggedIn) {
            // For guests, ensure cart is completely empty
            console.log('🧹 Guest detected - clearing cart');
            localStorage.removeItem('cart');
            localStorage.removeItem('appliedCoupon');
            localStorage.removeItem('appliedCouponMeta');
            localStorage.setItem('cart_owner_id', 'guest');
            
            // Force update badge to 0
            const badge = document.getElementById('cart-badge');
            if (badge) {
                badge.textContent = '0';
                console.log('✅ Badge cleared to 0');
            }
        }
    }
    
    // Global cart badge update function
    function forceUpdateAllCartBadges() {
        console.log('🔄 Force updating all cart badges...');
        
        // Get cart from localStorage
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
        
        console.log('📊 Cart data:', { items: cart.length, totalQuantity: totalItems });
        
        // Find ALL possible cart badge elements
        const selectors = [
            '#cart-badge',
            '.cart-badge', 
            '#cart-count',
            '.cart-count',
            '[data-cart-badge]',
            '.badge'
        ];
        
        let updated = 0;
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                // Only update elements that look like cart badges
                if (element && (
                    element.id.includes('cart') || 
                    element.className.includes('cart') ||
                    element.closest('.cart') ||
                    element.getAttribute('data-cart-badge')
                )) {
                    const oldValue = element.textContent;
                    element.textContent = totalItems;
                    console.log(`✅ Updated ${selector}: ${oldValue} → ${totalItems}`);
                    updated++;
                }
            });
        });
        
        console.log(`🎯 Updated ${updated} cart badge elements with value: ${totalItems}`);
        return totalItems;
    }
    
    // Clear guest cart IMMEDIATELY when script loads (before DOM render)
    (function() {
        const userMeta = document.querySelector('meta[name="user-id"]');
        const userId = userMeta ? String(userMeta.getAttribute('content') || '').trim() : '';
        if (!userId) {
            // Guest - clear cart immediately
            localStorage.removeItem('cart');
            localStorage.removeItem('appliedCoupon');
            localStorage.removeItem('appliedCouponMeta');
            localStorage.setItem('cart_owner_id', 'guest');
            console.log('⚡ Immediate guest cart clear executed');
        }
    })();
    
    // Clear and update when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        clearGuestCart();
        forceUpdateAllCartBadges();
    });
    
    // Update when page becomes visible
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            setTimeout(forceUpdateAllCartBadges, 100);
        }
    });
    
    // Listen for storage changes
    window.addEventListener('storage', (e) => {
        if (e.key === 'cart') {
            forceUpdateAllCartBadges();
        }
    });
    
    // Listen for custom cart events
    window.addEventListener('cartUpdated', forceUpdateAllCartBadges);
    
    // Force update every 5 seconds (reduced from 2s for better performance)
    setInterval(forceUpdateAllCartBadges, 5000);
    
    // Make function globally available
    window.forceUpdateCartBadges = forceUpdateAllCartBadges;
    
    console.log('🚀 Cart Badge Fix loaded - badges will update automatically');
    
})();