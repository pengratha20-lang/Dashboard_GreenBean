/**
 * Cart Management using Flask Backend
 * Instead of localStorage, we use Flask API endpoints for persistence
 */

document.addEventListener("DOMContentLoaded", () => {
    let cartItems = [];
    let appliedCoupon = null;
    let isLoading = false;

    // DOM Elements
    const cartBadge = document.getElementById('cart-badge');
    const cartItemsContainer = document.getElementById('cart-items-container');
    const emptyCartState = document.getElementById('empty-cart-state');
    const totalItemsSpan = document.getElementById('total-items');
    const subtotalSpan = document.getElementById('subtotal');
    const shippingCostSpan = document.getElementById('shipping-cost');
    const finalTotalSpan = document.getElementById('final-total');
    const checkoutBtn = document.getElementById('checkout-btn');
    const clearAllBtn = document.getElementById('clear-all-btn');
    const couponInput = document.getElementById('coupon-input');
    const applyCouponBtn = document.getElementById('apply-coupon-btn');

    // Shipping options
    const shippingOptions = document.querySelectorAll('input[name="shipping"]');

    // Constants
    const TAX_RATE = 0; // 0% tax
    const FREE_SHIPPING_THRESHOLD_USD = 50; // $50 USD
    const SHIPPING_COSTS = {
        'vireakbunthan-pp': 2.50,
        'vireakbunthan-prov': 5.00,
        'jnt-pp': 3.00,
        'jnt-prov': 6.00
    };

    // ===== FETCH CART FROM FLASK =====
    function loadCartFromFlask() {
        console.log('📡 Loading cart from Flask...');
        try {
            // Get cart data passed from Flask template
            if (window.cartDataFromFlask) {
                console.log('✅ Cart loaded from Flask:', window.cartDataFromFlask);
                return window.cartDataFromFlask;
            }
            
            console.warn('No cart data found from Flask');
            return [];
        } catch (error) {
            console.error('Error loading cart from Flask:', error);
            return [];
        }
    }

    // ===== INITIALIZATION =====
    function initializeCart() {
        console.log('🛒 Initializing Flask-based cart...');

        // Load cart data from Flask
        cartItems = loadCartFromFlask();
        console.log('✅ Cart items loaded from Flask:', cartItems);
        console.log('Cart items type:', Array.isArray(cartItems) ? 'Array' : typeof cartItems);
        console.log('Cart items count:', Array.isArray(cartItems) ? cartItems.length : 'N/A');
        
        // Ensure cartItems is always an array
        if (!Array.isArray(cartItems)) {
            console.warn('⚠️ cartItems is not an array, converting to empty array');
            cartItems = [];
        }

        // Display cart
        displayCartItems();
        updateCartSummary();
        updateCartBadge();
        setupEventListeners();
    }

    // ===== DISPLAY CART ITEMS =====
    function displayCartItems() {
        console.log('Displaying cart items:', cartItems.length);

        if (!cartItemsContainer || !emptyCartState) {
            console.error('Required DOM elements not found!');
            return;
        }

        // Clear previous items
        const existingItems = cartItemsContainer.querySelectorAll('.cart-item');
        existingItems.forEach(item => item.remove());

        if (cartItems.length === 0) {
            console.log('Cart is empty, showing empty state');
            emptyCartState.style.display = 'block';
            return;
        }

        console.log('Rendering', cartItems.length, 'items');
        emptyCartState.style.display = 'none';
        cartItemsContainer.style.display = 'block';

        const cartItemsHTML = cartItems.map(item => createCartItemHTML(item)).join('');
        emptyCartState.insertAdjacentHTML('afterend', cartItemsHTML);

        console.log('✅ Cart items displayed');
    }

    function createCartItemHTML(item) {
        const itemTotal = (item.price * item.quantity).toFixed(2);
        return `
            <div class="cart-item fade-in p-3 border-bottom" data-product-id="${item.id}">
                <div class="row align-items-center">
                    <div class="col-md-2">
                        <img src="${item.image}" alt="${item.name}" class="cart-item-image img-fluid rounded" style="width: 80px; height: 80px; object-fit: cover;">
                    </div>
                    <div class="col-md-4">
                        <h5 class="cart-item-title">${item.name}</h5>
                        <p class="cart-item-description">${item.description || 'Premium quality plant'}</p>
                        <div class="cart-item-meta">
                            <span class="badge bg-success me-2">${item.category || 'Plant'}</span>
                            ${item.inStock ? '<span class="badge bg-light text-dark">In Stock</span>' : '<span class="badge bg-warning">Limited Stock</span>'}
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="cart-item-price">$${item.price.toFixed(2)}</div>
                    </div>
                    <div class="col-md-3">
                        <div class="quantity-controls">
                            <button class="quantity-btn" data-action="decrease" ${item.quantity <= 1 ? 'disabled' : ''}>-</button>
                            <input type="number" class="quantity-input" value="${item.quantity}" min="1" max="99">
                            <button class="quantity-btn" data-action="increase" ${item.quantity >= 99 ? 'disabled' : ''}>+</button>
                        </div>
                        <div class="text-center mt-2">
                            <small class="text-muted">Total: $${itemTotal}</small>
                        </div>
                    </div>
                    <div class="col-md-1">
                        <button class="remove-item-btn" title="Remove item">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // ===== CART OPERATIONS =====
    async function removeFromCart(productId) {
        console.log('Removing product:', productId);

        try {
            const response = await fetch(`/remove-from-cart/${productId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                cartItems = data.cart_items || [];
                displayCartItems();
                updateCartSummary();
                updateCartBadge();
                showMessage('Item removed from cart', 'info');
            } else {
                showMessage(data.message || 'Error removing item', 'error');
            }
        } catch (error) {
            console.error('Error removing from cart:', error);
            showMessage('Error removing item', 'error');
        }
    }

    async function clearCart() {
        console.log('Clearing cart...');

        try {
            // Remove all items one by one
            for (let item of cartItems) {
                await fetch(`/remove-from-cart/${item.id}`, {
                    method: 'POST'
                });
            }

            cartItems = [];
            appliedCoupon = null;
            displayCartItems();
            updateCartSummary();
            updateCartBadge();
            showMessage('Cart cleared successfully!', 'success');
        } catch (error) {
            console.error('Error clearing cart:', error);
            showMessage('Error clearing cart', 'error');
        }
    }

    function updateCartSummary() {
        const subtotal = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);

        const selectedShipping = document.querySelector('input[name="shipping"]:checked');
        let shippingCost = selectedShipping ? (SHIPPING_COSTS[selectedShipping.value] || 0) : 0;

        const discountedSubtotal = subtotal;
        const tax = discountedSubtotal * TAX_RATE;
        const total = discountedSubtotal + shippingCost + tax;

        if (totalItemsSpan) totalItemsSpan.textContent = totalItems;
        if (subtotalSpan) subtotalSpan.textContent = '$' + subtotal.toFixed(2);
        if (shippingCostSpan) {
            shippingCostSpan.textContent = shippingCost === 0 ? 'Free' : '$' + shippingCost.toFixed(2);
        }
        if (finalTotalSpan) finalTotalSpan.textContent = '$' + total.toFixed(2);
    }

    function updateCartBadge() {
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        if (cartBadge) {
            cartBadge.textContent = totalItems;
        }
    }

    function setupEventListeners() {
        // Clear all button
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const clearModal = new bootstrap.Modal(document.getElementById('clearCartModal'));
                clearModal.show();
            });
        }

        const confirmClearBtn = document.getElementById('confirmClearBtn');
        if (confirmClearBtn) {
            confirmClearBtn.addEventListener('click', () => {
                const clearModal = bootstrap.Modal.getInstance(document.getElementById('clearCartModal'));
                clearModal.hide();
                clearCart();
            });
        }

        // Shipping options
        shippingOptions.forEach(option => {
            option.addEventListener('change', updateCartSummary);
        });

        // Cart item actions
        if (cartItemsContainer) {
            cartItemsContainer.addEventListener('click', handleCartItemActions);
            cartItemsContainer.addEventListener('input', handleQuantityChange);
        }

        // Checkout
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (cartItems.length > 0) {
                    window.location.href = '/checkout';
                } else {
                    showMessage('Your cart is empty!', 'warning');
                }
            });
        }
    }

    function handleCartItemActions(e) {
        const target = e.target;
        const cartItem = target.closest('.cart-item');

        if (!cartItem) return;

        const productId = cartItem.dataset.productId;

        if (target.classList.contains('remove-item-btn') || target.closest('.remove-item-btn')) {
            e.preventDefault();
            removeFromCart(productId);
        } else if (target.classList.contains('quantity-btn')) {
            e.preventDefault();
            const action = target.dataset.action;
            updateQuantity(productId, action);
        }
    }

    function handleQuantityChange(e) {
        if (e.target.classList.contains('quantity-input')) {
            const cartItem = e.target.closest('.cart-item');
            const productId = cartItem.dataset.productId;
            const newQuantity = parseInt(e.target.value) || 1;

            if (newQuantity > 0 && newQuantity <= 99) {
                updateQuantityDirect(productId, newQuantity);
            }
        }
    }

    function updateQuantity(productId, action) {
        const item = cartItems.find(i => String(i.id) === String(productId));
        if (!item) return;

        if (action === 'increase' && item.quantity < 99) {
            item.quantity += 1;
        } else if (action === 'decrease' && item.quantity > 1) {
            item.quantity -= 1;
        }

        syncCartToFlask();
        displayCartItems();
        updateCartSummary();
        updateCartBadge();
    }

    function updateQuantityDirect(productId, newQuantity) {
        const item = cartItems.find(i => String(i.id) === String(productId));
        if (!item) return;

        item.quantity = Math.max(1, Math.min(99, newQuantity));
        syncCartToFlask();
        updateCartSummary();
        updateCartBadge();
    }

    async function syncCartToFlask() {
        console.log('💾 Syncing cart to Flask...');

        try {
            const response = await fetch('/sync-cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    cart_items: cartItems,
                    coupon_code: appliedCoupon ? appliedCoupon.code : null
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log('✅ Cart synced to Flask');
                // Update cart_items from response if available
                if (data.cart_items) {
                    cartItems = data.cart_items;
                }
            } else {
                console.warn('Failed to sync cart:', data.message);
            }
        } catch (error) {
            console.error('Error syncing cart to Flask:', error);
        }
    }

    function showMessage(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type];

        const messageElement = document.createElement('div');
        messageElement.className = `alert ${alertClass} alert-dismissible fade show`;
        messageElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('main');
        if (container) {
            container.insertBefore(messageElement, container.firstChild);
            setTimeout(() => messageElement.remove(), 4000);
        }
    }

    // ===== INITIALIZE =====
    initializeCart();

    window.cartDebug = {
        getItems: () => cartItems,
        syncToFlask: syncCartToFlask,
        displayItems: displayCartItems,
        updateBadge: updateCartBadge
    };
});
