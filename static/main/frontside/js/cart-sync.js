(function () {
    'use strict';

    const CART_KEY = 'cart';
    const CART_OWNER_KEY = 'cart_owner_id';
    const AUTH_CART_HISTORY_KEY = 'cart_had_authenticated_owner';
    let isBootstrapping = false;
    let persistTimer = null;

    function getCurrentUserId() {
        const meta = document.querySelector('meta[name="user-id"]');
        return meta ? String(meta.getAttribute('content') || '').trim() : '';
    }

    function isLoggedIn() {
        return Boolean(getCurrentUserId());
    }

    function getLocalCart() {
        try {
            return JSON.parse(localStorage.getItem(CART_KEY)) || [];
        } catch (error) {
            return [];
        }
    }

    function setLocalCart(cartItems, ownerId) {
        isBootstrapping = true;
        localStorage.setItem(CART_KEY, JSON.stringify(cartItems || []));
        localStorage.setItem(CART_OWNER_KEY, ownerId || 'guest');
        if (ownerId && ownerId !== 'guest') {
            localStorage.setItem(AUTH_CART_HISTORY_KEY, '1');
        }
        window.dispatchEvent(new CustomEvent('cartUpdated', {
            detail: { items: cartItems || [], action: 'sync' }
        }));
        setTimeout(() => {
            isBootstrapping = false;
        }, 0);
    }

    function clearGuestLeakIfNeeded() {
        const ownerId = localStorage.getItem(CART_OWNER_KEY);
        const hadAuthenticatedCart = localStorage.getItem(AUTH_CART_HISTORY_KEY) === '1';
        if ((ownerId && ownerId !== 'guest') || hadAuthenticatedCart) {
            localStorage.removeItem(CART_KEY);
            localStorage.removeItem('appliedCoupon');
            localStorage.removeItem('appliedCouponMeta');
            localStorage.setItem(CART_OWNER_KEY, 'guest');
            localStorage.removeItem(AUTH_CART_HISTORY_KEY);
            window.dispatchEvent(new CustomEvent('cartUpdated', {
                detail: { items: [], action: 'logout-clear' }
            }));
        }
    }

    function clearGuestCartOnInit() {
        // If user is not logged in, ensure cart is empty
        const currentUserId = getCurrentUserId();
        if (!currentUserId) {
            const ownerId = localStorage.getItem(CART_OWNER_KEY);
            // If cart was owned by authenticated user, clear it
            if (ownerId && ownerId !== 'guest') {
                localStorage.removeItem(CART_KEY);
                localStorage.removeItem('appliedCoupon');
                localStorage.removeItem('appliedCouponMeta');
                localStorage.setItem(CART_OWNER_KEY, 'guest');
                window.dispatchEvent(new CustomEvent('cartUpdated', {
                    detail: { items: [], action: 'guest-clear' }
                }));
            }
        }
    }

    async function bootstrapAccountCart() {
        const currentUserId = getCurrentUserId();
        if (!currentUserId) {
            clearGuestLeakIfNeeded();
            return;
        }

        try {
            const response = await fetch('/api/cart/bootstrap', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    cart_items: getLocalCart(),
                    local_owner_id: localStorage.getItem(CART_OWNER_KEY) || 'guest'
                })
            });

            if (!response.ok) {
                return;
            }

            const data = await response.json();
            if (!data.success) {
                return;
            }

            setLocalCart(data.cart_items || [], data.owner_id || currentUserId);
        } catch (error) {
            console.error('Failed to bootstrap account cart:', error);
        }
    }

    async function persistAccountCart(cartItems) {
        if (!isLoggedIn() || isBootstrapping) {
            return;
        }

        try {
            const response = await fetch('/api/cart/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    cart_items: Array.isArray(cartItems) ? cartItems : getLocalCart()
                })
            });

            if (!response.ok) {
                return;
            }

            const data = await response.json();
            if (data.success) {
                setLocalCart(data.cart_items || [], getCurrentUserId());
            }
        } catch (error) {
            console.error('Failed to persist account cart:', error);
        }
    }

    function schedulePersist() {
        if (!isLoggedIn() || isBootstrapping) {
            return;
        }

        clearTimeout(persistTimer);
        persistTimer = setTimeout(() => {
            persistAccountCart(getLocalCart());
        }, 250);
    }

    const originalSetItem = Storage.prototype.setItem;
    Storage.prototype.setItem = function (key, value) {
        originalSetItem.apply(this, [key, value]);

        if (this !== localStorage || key !== CART_KEY || isBootstrapping) {
            return;
        }

        if (isLoggedIn()) {
            originalSetItem.apply(localStorage, [CART_OWNER_KEY, getCurrentUserId()]);
            originalSetItem.apply(localStorage, [AUTH_CART_HISTORY_KEY, '1']);
            schedulePersist();
        } else if (!localStorage.getItem(CART_OWNER_KEY)) {
            originalSetItem.apply(localStorage, [CART_OWNER_KEY, 'guest']);
        }
    };

    const originalRemoveItem = Storage.prototype.removeItem;
    Storage.prototype.removeItem = function (key) {
        originalRemoveItem.apply(this, [key]);

        if (this !== localStorage || key !== CART_KEY || isBootstrapping) {
            return;
        }

        originalSetItem.apply(localStorage, [CART_OWNER_KEY, isLoggedIn() ? getCurrentUserId() : 'guest']);
        schedulePersist();
    };

    document.addEventListener('DOMContentLoaded', () => {
        // First, clear guest cart if user is not logged in
        clearGuestCartOnInit();
        // Then, bootstrap account cart if user is logged in
        bootstrapAccountCart();
    });
    
    // Also clear immediately on script load for early initialization
    if (document.readyState === 'loading') {
        clearGuestCartOnInit();
    }
    window.addEventListener('cartUpdated', schedulePersist);
    window.addEventListener('beforeunload', () => {
        if (persistTimer) {
            clearTimeout(persistTimer);
        }
    });

    window.persistAccountCart = persistAccountCart;
})();
