// Cart Badge Fix - Force Update All Cart Badges
(function() {
    'use strict';
    
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
    
    // Update immediately when script loads
    document.addEventListener('DOMContentLoaded', forceUpdateAllCartBadges);
    
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
    
    // Force update every 2 seconds (remove this in production)
    setInterval(forceUpdateAllCartBadges, 2000);
    
    // Make function globally available
    window.forceUpdateCartBadges = forceUpdateAllCartBadges;
    
    console.log('🚀 Cart Badge Fix loaded - badges will update automatically');
    
})();