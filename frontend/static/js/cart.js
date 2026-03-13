document.addEventListener("DOMContentLoaded", () => {
    // Global cart management
    let cartItems = [];
    let isLoading = false;
    
    // Force load cart from localStorage
    function loadCartData() {
        const storedCart = localStorage.getItem('cart');
        console.log('Cart.js - Raw localStorage data:', storedCart);
        cartItems = JSON.parse(storedCart) || [];
        console.log('Cart.js - Parsed cartItems:', cartItems);
        return cartItems;
    }
    
    // Load cart data immediately
    loadCartData();

    // Add page visibility change listener to refresh cart
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            console.log('Cart.js - Page became visible, refreshing cart...');
            loadCartData();
            displayCartItems();
            updateCartSummary();
            updateCartBadge();
        }
    });

    // DOM Elements with existence check
    const cartBadge = document.getElementById('cart-badge');
    const cartItemsContainer = document.getElementById('cart-items-container');
    const emptyCartState = document.getElementById('empty-cart-state');
    const totalItemsSpan = document.getElementById('total-items');
    const subtotalSpan = document.getElementById('subtotal');
    const shippingCostSpan = document.getElementById('shipping-cost');
    const taxAmountSpan = document.getElementById('tax-amount');
    const finalTotalSpan = document.getElementById('final-total');
    const checkoutBtn = document.getElementById('checkout-btn');
    const clearAllBtn = document.getElementById('clear-all-btn');
    const couponInput = document.getElementById('coupon-input');
    const applyCouponBtn = document.getElementById('apply-coupon-btn');
    const recommendedProductsContainer = document.getElementById('recommended-products');
    
    // Debug DOM elements
    console.log('Cart.js - DOM Elements Check:');
    console.log('- cartBadge:', !!cartBadge);
    console.log('- cartItemsContainer:', !!cartItemsContainer);
    console.log('- emptyCartState:', !!emptyCartState);
    console.log('- totalItemsSpan:', !!totalItemsSpan);
    console.log('- checkoutBtn:', !!checkoutBtn);

    // Shipping options
    const shippingOptions = document.querySelectorAll('input[name="shipping"]');
    
    // Constants
    const TAX_RATE = 0.08; // 8% tax rate
    const FREE_SHIPPING_THRESHOLD = 100000; // 100,000 Riel
    const SHIPPING_COSTS = {
        'vireakbunthan-pp': 2500,      // Vireakbunthan - Phnom Penh: 2,500 Riel
        'vireakbunthan-prov': 5000,    // Vireakbunthan - Provinces: 5,000 Riel
        'jnt-pp': 3000,                // J&T Express - Phnom Penh: 3,000 Riel
        'jnt-prov': 6000               // J&T Express - Provinces: 6,000 Riel
    };

    // Coupon codes
    const COUPON_CODES = {
        'WELCOME10': { discount: 0.10, type: 'percentage', description: '10% off' },
        'PLANT20': { discount: 0.20, type: 'percentage', description: '20% off' },
        'SAVE5': { discount: 5, type: 'fixed', description: '$5 off' },
        'FREESHIP': { discount: 0, type: 'freeship', description: 'Free shipping' }
    };

    let appliedCoupon = null;

    // Initialize cart with delay to ensure DOM is ready
    setTimeout(initializeCart, 100);
    
    // Also make global function for manual refresh
    window.refreshCart = function() {
        console.log('Manual cart refresh called');
        loadCartData();
        initializeCart();
    };
    
    // Test function to force display cart items
    window.testDisplayCart = function() {
        console.log('🧪 Test display cart called');
        
        // Force load data
        const rawCart = localStorage.getItem('cart');
        console.log('Raw localStorage cart:', rawCart);
        
        if (!rawCart) {
            console.log('No cart data found in localStorage');
            return;
        }
        
        const testCart = JSON.parse(rawCart);
        console.log('Parsed cart data:', testCart);
        
        // Force update cartItems
        cartItems.length = 0;
        cartItems.push(...testCart);
        
        console.log('Updated cartItems:', cartItems);
        
        // Force display
        displayCartItems();
        updateCartSummary();
        updateCartBadge();
    };
    
    function initializeCart() {
        // Debug logging
        console.log('Cart.js - Initializing cart...');
        
        // Reload cart data to make sure we have the latest
        loadCartData();
        console.log('Cart.js - After reload - cartItems:', cartItems);
        console.log('Cart.js - After reload - cartItems length:', cartItems.length);
        
        displayCartItems();
        updateCartSummary();
        setupEventListeners();
        loadRecommendedProducts();
        updateCartBadge();
        
        console.log('Cart.js - Initialization complete');
    }

    function setupEventListeners() {
        // Checkout button
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', function(e) {
                e.preventDefault();
                handleCheckout();
            });
        }

        // Clear all button
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', clearCart);
        }

        // Coupon application
        if (applyCouponBtn && couponInput) {
            applyCouponBtn.addEventListener('click', applyCoupon);
            couponInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    applyCoupon();
                }
            });
        }

        // Shipping options
        shippingOptions.forEach(option => {
            option.addEventListener('change', updateCartSummary);
        });

        // Cart item actions (using event delegation)
        if (cartItemsContainer) {
            cartItemsContainer.addEventListener('click', handleCartItemActions);
            cartItemsContainer.addEventListener('input', handleQuantityChange);
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

    function displayCartItems() {
        console.log('Cart.js - displayCartItems called');
        console.log('Cart.js - cartItemsContainer exists:', !!cartItemsContainer);
        console.log('Cart.js - emptyCartState exists:', !!emptyCartState);
        console.log('Cart.js - cartItems:', cartItems);
        console.log('Cart.js - cartItems.length:', cartItems.length);
        
        if (!cartItemsContainer) {
            console.error('Cart.js - cartItemsContainer not found!');
            return;
        }

        if (!emptyCartState) {
            console.error('Cart.js - emptyCartState not found!');
            return;
        }

        if (cartItems.length === 0) {
            console.log('Cart.js - Showing empty cart state');
            if (emptyCartState) emptyCartState.style.display = 'block';
            const existingList = cartItemsContainer.querySelector('.cart-items-list');
            if (existingList) existingList.style.display = 'none';
            return;
        }

        console.log('Cart.js - Showing cart items');
        if (emptyCartState) emptyCartState.style.display = 'none';
        
        const cartItemsHTML = cartItems.map(item => createCartItemHTML(item)).join('');
        console.log('Cart.js - Generated HTML length:', cartItemsHTML.length);
        console.log('Cart.js - Sample HTML:', cartItemsHTML.substring(0, 200));
        
        cartItemsContainer.innerHTML = `
            <div class="cart-items-list">
                ${cartItemsHTML}
            </div>
        `;
        
        console.log('Cart.js - Cart items displayed successfully');
    }

    /**
     * Creates HTML for a cart item
     * @param {Object} item - The cart item object
     * @param {string} item.id - Product ID
     * @param {string} item.name - Product name
     * @param {number} item.price - Product price
     * @param {number} item.quantity - Item quantity
     * @param {string} item.image - Product image URL
     * @param {number} [item.originalPrice] - Original price if on sale
     * @param {string} [item.description] - Product description
     * @param {string} [item.category] - Product category
     * @param {boolean} [item.inStock] - Stock status
     * @returns {string} HTML string for the cart item
     */
    function createCartItemHTML(item) {
        const itemTotal = (item.price * item.quantity).toLocaleString('en-US', { maximumFractionDigits: 0 });
        const discountPercentage = item.originalPrice ? Math.round(((item.originalPrice - item.price) / item.originalPrice) * 100) : 0;
        
        return `
            <div class="cart-item fade-in p-3 border-bottom" data-product-id="${item.id}">
                <div class="row align-items-center">
                    <div class="col-md-2">
                        <div class="position-relative">
                            <img src="${item.image}" alt="${item.name}" class="cart-item-image img-fluid rounded" style="width: 80px; height: 80px; object-fit: cover;">
                            ${discountPercentage > 0 ? `<span class="discount-badge">-${discountPercentage}%</span>` : ''}
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="cart-item-details">
                            <h5 class="cart-item-title">${item.name}</h5>
                            <p class="cart-item-description">${item.description || 'Premium quality plant for your home or garden.'}</p>
                            <div class="cart-item-meta">
                                <span class="badge bg-success me-2">${item.category || 'Plant'}</span>
                                ${item.inStock ? '<span class="badge bg-light text-dark">In Stock</span>' : '<span class="badge bg-warning">Limited Stock</span>'}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="cart-item-price">
                            ${item.originalPrice ? `<span class="cart-item-price-original">\u20a8${item.originalPrice.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>` : ''}
                            \u20a8${item.price.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="quantity-controls">
                            <button class="quantity-btn" data-action="decrease" ${item.quantity <= 1 ? 'disabled' : ''}>-</button>
                            <input type="number" class="quantity-input" value="${item.quantity}" min="1" max="99">
                            <button class="quantity-btn" data-action="increase" ${item.quantity >= 99 ? 'disabled' : ''}>+</button>
                        </div>
                        <div class="text-center mt-2">
                            <small class="text-muted">Total: \u20a8${itemTotal}</small>
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

    function updateQuantity(productId, action) {
        const itemIndex = cartItems.findIndex(item => item.id === productId);
        if (itemIndex === -1) return;

        const item = cartItems[itemIndex];
        
        if (action === 'increase' && item.quantity < 99) {
            item.quantity += 1;
        } else if (action === 'decrease' && item.quantity > 1) {
            item.quantity -= 1;
        }

        saveCartToStorage();
        displayCartItems();
        updateCartSummary();
        updateCartBadge();
        showMessage('Cart updated successfully!', 'success');
    }

    function updateQuantityDirect(productId, newQuantity) {
        const itemIndex = cartItems.findIndex(item => item.id === productId);
        if (itemIndex === -1) return;

        cartItems[itemIndex].quantity = Math.max(1, Math.min(99, newQuantity));
        
        saveCartToStorage();
        updateCartSummary();
        updateCartBadge();
    }

    function removeFromCart(productId) {
        const itemIndex = cartItems.findIndex(item => item.id === productId);
        if (itemIndex === -1) return;

        // Add slide-out animation
        const cartItemElement = document.querySelector(`[data-product-id="${productId}"]`);
        if (cartItemElement) {
            cartItemElement.classList.add('slide-out');
            setTimeout(() => {
                cartItems.splice(itemIndex, 1);
                saveCartToStorage();
                displayCartItems();
                updateCartSummary();
                updateCartBadge();
                showMessage('Item removed from cart', 'info');
            }, 300);
        }
    }

    function clearCart() {
        if (cartItems.length === 0) {
            showMessage('Cart is already empty!', 'info');
            return;
        }

        if (confirm('Are you sure you want to remove all items from your cart?')) {
            cartItems = [];
            appliedCoupon = null;
            saveCartToStorage();
            displayCartItems();
            updateCartSummary();
            updateCartBadge();
            
            // Dispatch custom event for cross-page synchronization
            window.dispatchEvent(new CustomEvent('cartUpdated', {
                detail: { items: cartItems, action: 'clear' }
            }));
            
            showMessage('Cart cleared successfully!', 'success');
        }
    }

    function updateCartSummary() {
        console.log('Updating cart summary, cart items:', cartItems.length);
        
        const subtotal = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        
        // Get selected shipping cost using value attribute
        const selectedShipping = document.querySelector('input[name="shipping"]:checked');
        let shippingCost = 0;
        let shippingLabel = 'Free';
        
        console.log('Selected shipping option:', selectedShipping?.value);
        
        if (selectedShipping && selectedShipping.value) {
            shippingCost = SHIPPING_COSTS[selectedShipping.value] || 0;
            shippingLabel = selectedShipping.nextElementSibling?.textContent || 'Delivery';
        }

        console.log('Calculated shipping cost:', shippingCost);

        // Apply free shipping only for J&T if over threshold, or if coupon applied
        if (appliedCoupon && appliedCoupon.type === 'freeship') {
            shippingCost = 0;
            console.log('Free shipping applied via coupon');
        } else if (subtotal >= FREE_SHIPPING_THRESHOLD && selectedShipping?.value === 'vireakbunthan-pp') {
            shippingCost = 0;
            console.log('Free Phnom Penh delivery applied (over 100,000\u20a8)');
        }

        // Calculate discount
        let discount = 0;
        if (appliedCoupon) {
            if (appliedCoupon.type === 'percentage') {
                discount = subtotal * appliedCoupon.discount;
            } else if (appliedCoupon.type === 'fixed') {
                discount = appliedCoupon.discount;
            }
        }

        const discountedSubtotal = Math.max(0, subtotal - discount);
        const tax = discountedSubtotal * TAX_RATE;
        const total = discountedSubtotal + shippingCost + tax;

        console.log('Summary calculation:', { subtotal, shippingCost, tax, total });

        // Update DOM elements with Riel currency
        if (totalItemsSpan) totalItemsSpan.textContent = totalItems;
        if (subtotalSpan) subtotalSpan.textContent = `\u20a8${subtotal.toLocaleString('en-US')}`;
        if (shippingCostSpan) {
            if (shippingCost === 0) {
                shippingCostSpan.textContent = 'Free';
                shippingCostSpan.classList.add('text-success');
            } else {
                shippingCostSpan.textContent = `\u20a8${shippingCost.toLocaleString('en-US')}`;
                shippingCostSpan.classList.remove('text-success');
            }
            console.log('Updated shipping display:', shippingCostSpan.textContent);
        }
        if (taxAmountSpan) taxAmountSpan.textContent = `\u20a8${tax.toLocaleString('en-US', { minimumFractionDigits: 0 })}`;
        if (finalTotalSpan) finalTotalSpan.textContent = `\u20a8${total.toLocaleString('en-US', { minimumFractionDigits: 0 })}`;

        // Enable/disable checkout button
        if (checkoutBtn) {
            if (cartItems.length === 0) {
                checkoutBtn.classList.add('disabled');
                checkoutBtn.style.pointerEvents = 'none';
                checkoutBtn.classList.remove('btn-success');
                checkoutBtn.classList.add('btn-secondary');
            } else {
                checkoutBtn.classList.remove('disabled');
                checkoutBtn.style.pointerEvents = 'auto';
                checkoutBtn.classList.remove('btn-secondary');
                checkoutBtn.classList.add('btn-success');
            }
        }

        // Show discount if applied
        displayAppliedDiscount(discount);
    }

    function displayAppliedDiscount(discount) {
        const existingDiscount = document.querySelector('.discount-row');
        if (existingDiscount) {
            existingDiscount.remove();
        }

        if (discount > 0 && appliedCoupon) {
            const discountHTML = `
                <div class="summary-item discount-row d-flex justify-content-between mb-3 text-success">
                    <span>Discount (${appliedCoupon.description}):</span>
                    <span>-\u20a8${discount.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
                </div>
            `;
            
            const taxRow = document.querySelector('.summary-item:last-of-type');
            if (taxRow) {
                taxRow.insertAdjacentHTML('beforebegin', discountHTML);
            }
        }
    }

    function applyCoupon() {
        const couponCode = couponInput.value.trim().toUpperCase();
        
        if (!couponCode) {
            showMessage('Please enter a coupon code', 'warning');
            return;
        }

        if (COUPON_CODES[couponCode]) {
            if (appliedCoupon && appliedCoupon.code === couponCode) {
                showMessage('This coupon is already applied', 'info');
                return;
            }

            appliedCoupon = { ...COUPON_CODES[couponCode], code: couponCode };
            updateCartSummary();
            showMessage(`Coupon applied! ${appliedCoupon.description}`, 'success');
            
            // Update coupon display
            const appliedCouponDisplay = document.getElementById('applied-coupon-display');
            const appliedCouponText = document.getElementById('applied-coupon-text');
            
            // Hide input section
            couponInput.closest('.input-group').style.display = 'none';
            applyCouponBtn.style.display = 'none';
            
            // Show applied coupon
            if (appliedCouponDisplay) {
                appliedCouponText.textContent = `✓ ${couponCode} - ${appliedCoupon.description}`;
                appliedCouponDisplay.style.display = 'block';
                
                // Attach remove event listener
                const removeCouponBtn = document.getElementById('remove-coupon-btn');
                if (removeCouponBtn) {
                    removeCouponBtn.addEventListener('click', removeCoupon);
                }
            }
            
        } else {
            showMessage('Invalid coupon code', 'error');
        }
    }

    function removeCoupon() {
        appliedCoupon = null;
        updateCartSummary();
        
        // Reset coupon display
        couponInput.value = '';
        couponInput.closest('.input-group').style.display = 'flex';
        applyCouponBtn.style.display = 'inline-block';
        
        const appliedCouponDisplay = document.getElementById('applied-coupon-display');
        if (appliedCouponDisplay) {
            appliedCouponDisplay.style.display = 'none';
        }
        
        showMessage('Coupon removed', 'info');
        
        showMessage('Coupon removed', 'info');
    }

    function handleCheckout() {
        console.log('Checkout button clicked, cart items:', cartItems);
        
        if (cartItems.length === 0) {
            showMessage('Your cart is empty!', 'warning');
            return;
        }

        if (isLoading) {
            console.log('Checkout already in progress, returning');
            return;
        }

        isLoading = true;
        
        // Add loading state
        if (checkoutBtn) {
            const originalContent = checkoutBtn.innerHTML;
            checkoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Preparing Checkout...';
            checkoutBtn.classList.add('disabled');
        }

        console.log('Syncing cart to session:', cartItems);

        // Sync cart to session before checkout, including applied coupon (if any)
        fetch('/sync-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                cart_items: cartItems,
                coupon_code: appliedCoupon ? appliedCoupon.code : null
            })
        })
        .then(response => {
            console.log('Sync response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Sync response data:', data);
            if (data.success) {
                console.log('Cart synced successfully, redirecting to checkout');
                // Small delay before redirect to ensure state is updated
                setTimeout(() => {
                    window.location.href = '/checkout';
                }, 500);
            } else {
                throw new Error(data.message || 'Failed to sync cart');
            }
        })
        .catch(error => {
            console.error('Checkout error:', error);
            // Reset button state on error
            if (checkoutBtn) {
                checkoutBtn.innerHTML = '<i class="fas fa-credit-card me-2"></i>Proceed to Checkout';
                checkoutBtn.classList.remove('disabled');
            }
            isLoading = false;
            showMessage('Error preparing checkout. Please try again.', 'error');
        });
    }

    function getSelectedShippingCost() {
        const selectedShipping = document.querySelector('input[name="shipping"]:checked');
        return selectedShipping ? SHIPPING_COSTS[selectedShipping.id] || 0 : 0;
    }

    function loadRecommendedProducts() {
        // Sample recommended products - using actual available images from your static folder
        const recommendedProducts = [
            {
                id: 'rec-1',
                name: 'Rubber Plant',
                price: 28.00,
                image: '/static/images/indoor/Dracaena_plants.jpg',
                rating: 4.8
            },
            {
                id: 'rec-2',
                name: 'Aloe Vera',
                price: 15.00,
                image: '/static/images/indoor/golden_potho.jpg',
                rating: 4.9
            },
            {
                id: 'rec-3',
                name: 'Boston Fern',
                price: 22.00,
                image: '/static/images/indoor/ZZ_plants.jpg',
                rating: 4.6
            },
            {
                id: 'rec-4',
                name: 'Spider Plant',
                price: 18.00,
                image: '/static/images/indoor/Lucky_Bamboo.jpg',
                rating: 4.7
            }
        ];

        if (recommendedProductsContainer) {
            const productsHTML = recommendedProducts.map(product => `
                <div class="col-md-3 col-sm-6 mb-4">
                    <div class="card h-100 border-0 shadow-sm recommended-product">
                        <img src="${product.image}" class="card-img-top" alt="${product.name}" style="height: 200px; object-fit: cover;">
                        <div class="card-body">
                            <h6 class="card-title">${product.name}</h6>
                            <div class="rating mb-2">
                                ${generateStarRating(product.rating)}
                                <small class="text-muted ms-1">(${product.rating})</small>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="h6 text-success mb-0">\u20a8${(product.price * 4000).toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
                                <button class="btn btn-outline-success btn-sm add-recommended-btn" data-product-id="${product.id}">
                                    <i class="fas fa-plus"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');

            recommendedProductsContainer.innerHTML = productsHTML;

            // Add event listeners for recommended products
            recommendedProductsContainer.addEventListener('click', (e) => {
                if (e.target.closest('.add-recommended-btn')) {
                    const productId = e.target.closest('.add-recommended-btn').dataset.productId;
                    const product = recommendedProducts.find(p => p.id === productId);
                    if (product) {
                        addRecommendedToCart(product);
                    }
                }
            });
        }
    }

    function generateStarRating(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 !== 0;
        let starsHTML = '';

        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<i class="fas fa-star text-warning"></i>';
        }

        if (hasHalfStar) {
            starsHTML += '<i class="fas fa-star-half-alt text-warning"></i>';
        }

        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        for (let i = 0; i < emptyStars; i++) {
            starsHTML += '<i class="far fa-star text-warning"></i>';
        }

        return starsHTML;
    }

    function addRecommendedToCart(product) {
        const existingItem = cartItems.find(item => item.id === product.id);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cartItems.push({
                ...product,
                quantity: 1,
                category: 'Indoor',
                inStock: true
            });
        }

        saveCartToStorage();
        displayCartItems();
        updateCartSummary();
        updateCartBadge();
        showMessage(`${product.name} added to cart!`, 'success');
    }

    function updateCartBadge() {
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        if (cartBadge) {
            cartBadge.textContent = totalItems;
        }
    }

    function saveCartToStorage() {
        localStorage.setItem('cart', JSON.stringify(cartItems));
    }

    function showMessage(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type];

        const messageElement = document.createElement('div');
        messageElement.className = 'cart-message';
        messageElement.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        document.body.appendChild(messageElement);

        // Auto remove after 4 seconds
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.remove();
            }
        }, 4000);
    }

    // Load cart from other pages
    window.addEventListener('storage', (e) => {
        if (e.key === 'cart') {
            console.log('Cart.js - Storage event detected');
            loadCartData();
            displayCartItems();
            updateCartSummary();
            updateCartBadge();
        }
    });

    // Listen for custom cart events from other pages
    window.addEventListener('cartUpdated', (e) => {
        console.log('Cart.js - cartUpdated event received:', e.detail);
        const { items, action } = e.detail;
        
        // Reload from localStorage to be sure
        loadCartData();
        
        displayCartItems();
        updateCartSummary();
        updateCartBadge();
        
        // Show appropriate message based on action
        if (action === 'add') {
            showMessage('Item added to cart!', 'success');
        } else if (action === 'clear') {
            showMessage('Cart cleared!', 'info');
        }
    });

    // Global function to add items from other pages
    window.addToCart = function(productData) {
        const existingItem = cartItems.find(item => item.id === productData.id);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cartItems.push({
                ...productData,
                quantity: 1,
                inStock: true
            });
        }

        saveCartToStorage();
        updateCartBadge();
        
        // Update cart page if currently viewing it
        if (window.location.pathname.includes('cart.html')) {
            displayCartItems();
            updateCartSummary();
        }
        
        // Dispatch custom event for cross-page synchronization
        window.dispatchEvent(new CustomEvent('cartUpdated', {
            detail: { items: cartItems, action: 'add', product: productData }
        }));
        
        return true;
    };

    // Global function to get cart items
    window.getCartItems = function() {
        return cartItems;
    };

    // Global function to get cart total
    window.getCartTotal = function() {
        return cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    };

    // Global function to clear cart from other pages
    window.clearCart = function() {
        if (cartItems.length === 0) {
            return false;
        }

        cartItems = [];
        appliedCoupon = null;
        saveCartToStorage();
        updateCartBadge();
        
        // Update cart page if currently viewing it
        if (window.location.pathname.includes('cart.html')) {
            displayCartItems();
            updateCartSummary();
        }
        
        // Dispatch custom event for cross-page synchronization
        window.dispatchEvent(new CustomEvent('cartUpdated', {
            detail: { items: cartItems, action: 'clear' }
        }));
        
        return true;
    };
});