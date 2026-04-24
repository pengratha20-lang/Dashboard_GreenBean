document.addEventListener("DOMContentLoaded", () => {
    // Global cart management
    let cartItems = [];
    let isLoading = false;
    
    // IMPORTANT: Cart uses localStorage (browser storage), NOT session cookies
    // Clearing cookies will NOT clear the cart. You must also clear localStorage.
    
    // CURRENCY SETTINGS - USD ONLY
    const EXCHANGE_RATE = 4100; // 1 USD = 4,100 KHR (reference only)
    let currentCurrency = 'USD'; // Always USD
    
    // Force load cart from localStorage
    function loadCartData() {
        const storedCart = localStorage.getItem('cart');
        cartItems = JSON.parse(storedCart) || [];

        const storedCouponMeta = localStorage.getItem('appliedCouponMeta');
        appliedCoupon = null;
        if (storedCouponMeta) {
            try {
                appliedCoupon = JSON.parse(storedCouponMeta);
            } catch (error) {
                localStorage.removeItem('appliedCouponMeta');
                localStorage.removeItem('appliedCoupon');
            }
        }

        return cartItems;
    }
    
    // Load cart data immediately
    loadCartData();

    // Add page visibility change listener to refresh cart
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            loadCartData();
            displayCartItems();
            updateCartSummary();
            updateCartBadge();
        } else {
            // Page is hidden - reset loading state to prevent stuck buttons
            if (isLoading && checkoutBtn) {
                isLoading = false;
                checkoutBtn.classList.remove('disabled');
            }
        }
    });

    // Reset loading state if user clicks browser back button or navigates away
    window.addEventListener('beforeunload', () => {
        isLoading = false;
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
    
    // Shipping options
    const shippingOptions = document.querySelectorAll('input[name="shipping"]');
    
    // Constants
    const TAX_RATE = 0; // 0% tax rate (removed)
    const FREE_SHIPPING_THRESHOLD_USD = 50; // $50 USD
    const SHIPPING_COSTS = {
        'vireakbunthan-pp': 2.50,      // Vireakbunthan - Phnom Penh: $2.50
        'vireakbunthan-prov': 5.00,    // Vireakbunthan - Provinces: $5.00
        'jnt-pp': 3.00,                // J&T Express - Phnom Penh: $3.00
        'jnt-prov': 6.00               // J&T Express - Provinces: $6.00
    };

    let appliedCoupon = null;

    // ===== CURRENCY CONVERSION FUNCTIONS =====
    function formatPrice(amount, currency = 'USD') {
        // Always format as USD with $ symbol
        return '$' + amount.toFixed(2);
    }

    function getPriceInCurrentCurrency(usdAmount) {
        // Always return USD amount
        return usdAmount;
    }

    function changeCurrency(newCurrency) {
        // Currency is fixed to USD - no changing needed
    }
    // ===== END CURRENCY FUNCTIONS =====

    // Initialize cart with delay to ensure DOM is ready
    setTimeout(initializeCart, 100);
    

    
    function initializeCart() {
        // Reset loading state when cart page loads (user might have navigated back from checkout)
        isLoading = false;
        if (checkoutBtn) {
            checkoutBtn.classList.remove('disabled');
            checkoutBtn.innerHTML = '<i class="fas fa-credit-card me-2"></i>Proceed to Checkout';
        }
        
        // Reload cart data to make sure we have the latest
        loadCartData();
        
        displayCartItems();
        updateCartSummary();
        updateCouponDisplay();
        setupEventListeners();
        updateCartBadge();
        loadRecommendedProducts();
        
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
            clearAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                // Show confirmation modal instead of directly clearing
                const clearModal = new bootstrap.Modal(document.getElementById('clearCartModal'));
                clearModal.show();
            });
        }

        // Confirm clear button in modal
        const confirmClearBtn = document.getElementById('confirmClearBtn');
        if (confirmClearBtn) {
            confirmClearBtn.addEventListener('click', function() {
                const clearModal = bootstrap.Modal.getInstance(document.getElementById('clearCartModal'));
                clearModal.hide();
                clearCart(); // Now actually clear the cart
            });
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
        
        const productId = normalizeProductId(cartItem.dataset.productId);
        
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
            const productId = normalizeProductId(cartItem.dataset.productId);
            const newQuantity = parseInt(e.target.value) || 1;
            
            if (newQuantity > 0 && newQuantity <= 99) {
                updateQuantityDirect(productId, newQuantity);
            }
        }
    }

    function displayCartItems() {
        console.log('Cart.js - displayCartItems called');
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

        // Remove any previously rendered items
        const existingItems = cartItemsContainer.querySelectorAll('.cart-item');
        existingItems.forEach(item => item.remove());

        if (cartItems.length === 0) {
            console.log('Cart.js - Showing empty cart state');
            emptyCartState.style.display = 'block';
            // Make sure container is visible
            cartItemsContainer.style.display = 'block';
            return;
        }

        console.log('Cart.js - Showing cart items, count:', cartItems.length);
        emptyCartState.style.display = 'none';
        cartItemsContainer.style.display = 'block';
        
        const cartItemsHTML = cartItems.map(item => {
            const html = createCartItemHTML(item);
            console.log('Rendering item:', item.id, item.name);
            return html;
        }).join('');
        
        console.log('Cart.js - Generated HTML for all items, length:', cartItemsHTML.length);
        
        // Insert items after empty state (they will be visible since empty state is hidden)
        if (emptyCartState) {
            emptyCartState.insertAdjacentHTML('afterend', cartItemsHTML);
        } else {
            cartItemsContainer.insertAdjacentHTML('beforeend', cartItemsHTML);
        }
        
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
        const itemTotal = (item.price * item.quantity).toFixed(2);
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
                            ${item.originalPrice ? `<span class="cart-item-price-original">$${item.originalPrice.toFixed(2)}</span>` : ''}
                            $${item.price.toFixed(2)}
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="quantity-controls">
                            <button class="quantity-btn" data-action="decrease" ${item.quantity <= 1 ? 'disabled' : ''}>-</button>
                            <input type="number" class="quantity-input" value="${item.quantity}" min="1" max="99">
                            <button class="quantity-btn" data-action="increase" ${item.quantity >= 99 ? 'disabled' : ''}>+</button>
                        </div>
                        <div class="text-center mt-2">
                            <small class="text-muted">Total: $${(item.price * item.quantity).toFixed(2)}</small>
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

    function normalizeProductId(value) {
        const parsed = Number(value);
        return Number.isNaN(parsed) ? String(value) : parsed;
    }

    function updateQuantity(productId, action) {
        const normalizedProductId = normalizeProductId(productId);
        const itemIndex = cartItems.findIndex(item => normalizeProductId(item.id) === normalizedProductId);
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
        const normalizedProductId = normalizeProductId(productId);
        const itemIndex = cartItems.findIndex(item => normalizeProductId(item.id) === normalizedProductId);
        if (itemIndex === -1) return;

        cartItems[itemIndex].quantity = Math.max(1, Math.min(99, newQuantity));
        
        saveCartToStorage();
        updateCartSummary();
        updateCartBadge();
    }

    function removeFromCart(productId) {
        const normalizedProductId = normalizeProductId(productId);
        const itemIndex = cartItems.findIndex(item => normalizeProductId(item.id) === normalizedProductId);
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

        // User already confirmed via Bootstrap modal, so directly clear cart
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
        } else if (subtotal >= FREE_SHIPPING_THRESHOLD_USD && selectedShipping?.value === 'vireakbunthan-pp') {
            shippingCost = 0;
            console.log('Free Phnom Penh delivery applied (over $50)');
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

        // Update DOM elements with selected currency
        if (totalItemsSpan) totalItemsSpan.textContent = totalItems;
        if (subtotalSpan) subtotalSpan.textContent = formatPrice(getPriceInCurrentCurrency(subtotal));
        if (shippingCostSpan) {
            if (shippingCost === 0) {
                shippingCostSpan.textContent = 'Free';
                shippingCostSpan.classList.add('text-success');
            } else {
                shippingCostSpan.textContent = formatPrice(getPriceInCurrentCurrency(shippingCost));
                shippingCostSpan.classList.remove('text-success');
            }
            console.log('Updated shipping display:', shippingCostSpan.textContent);
        }
        if (taxAmountSpan) taxAmountSpan.textContent = formatPrice(getPriceInCurrentCurrency(tax));
        if (finalTotalSpan) finalTotalSpan.textContent = formatPrice(getPriceInCurrentCurrency(total));

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
                    <span>-${formatPrice(getPriceInCurrentCurrency(discount))}</span>
                </div>
            `;
            
            const taxRow = document.querySelector('.summary-item:last-of-type');
            if (taxRow) {
                taxRow.insertAdjacentHTML('beforebegin', discountHTML);
            }
        }
    }

    function updateCouponDisplay() {
        const appliedCouponDisplay = document.getElementById('applied-coupon-display');
        const appliedCouponText = document.getElementById('applied-coupon-text');

        if (!couponInput || !applyCouponBtn || !appliedCouponDisplay || !appliedCouponText) {
            return;
        }

        if (appliedCoupon) {
            couponInput.value = '';
            couponInput.closest('.input-group').style.display = 'none';
            applyCouponBtn.style.display = 'none';
            appliedCouponText.textContent = `Coupon: ${appliedCoupon.code} - ${appliedCoupon.description}`;
            appliedCouponDisplay.style.display = 'block';
        } else {
            couponInput.closest('.input-group').style.display = 'flex';
            applyCouponBtn.style.display = 'inline-block';
            appliedCouponDisplay.style.display = 'none';
        }

        const removeCouponBtn = document.getElementById('remove-coupon-btn');
        if (removeCouponBtn) {
            removeCouponBtn.onclick = removeCoupon;
        }
    }

    async function applyCoupon() {
        const couponCode = couponInput.value.trim().toUpperCase();

        if (!couponCode) {
            showMessage('Please enter a coupon code', 'warning');
            return;
        }

        if (appliedCoupon && appliedCoupon.code === couponCode) {
            showMessage('This coupon is already applied', 'info');
            return;
        }

        try {
            const subtotal = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            const response = await fetch('/api/cart/validate-coupon', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    coupon_code: couponCode,
                    subtotal: subtotal
                })
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Invalid coupon code');
            }

            appliedCoupon = data.coupon;
            saveCartToStorage();
            updateCartSummary();
            updateCouponDisplay();
            showMessage(`Coupon applied! ${appliedCoupon.description}`, 'success');
        } catch (error) {
            showMessage(error.message || 'Invalid coupon code', 'error');
        }
    }

    function removeCoupon() {
        appliedCoupon = null;
        saveCartToStorage();
        updateCartSummary();
        couponInput.value = '';
        updateCouponDisplay();
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
        const originalButton = checkoutBtn ? checkoutBtn.innerHTML : null;
        
        // Add loading state
        if (checkoutBtn) {
            checkoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Preparing Checkout...';
            checkoutBtn.classList.add('disabled');
        }

        console.log('Syncing cart to session:', cartItems);

        // Set a timeout to reset loading state if request takes too long (15 seconds)
        const timeoutId = setTimeout(() => {
            console.warn('Checkout request timeout - resetting button state');
            if (checkoutBtn && originalButton) {
                checkoutBtn.innerHTML = originalButton;
                checkoutBtn.classList.remove('disabled');
            }
            isLoading = false;
            showMessage('Checkout request took too long. Please try again.', 'error');
        }, 15000);

        // Sync cart to session before checkout, including applied coupon and selected currency
        fetch('/sync-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                cart_items: cartItems,
                coupon_code: appliedCoupon ? appliedCoupon.code : null,
                currency: currentCurrency
            })
        })
        .then(response => {
            clearTimeout(timeoutId);
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
            clearTimeout(timeoutId);
            console.error('Checkout error:', error);
            // Reset button state on error
            if (checkoutBtn && originalButton) {
                checkoutBtn.innerHTML = originalButton;
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

    async function loadRecommendedProducts() {
        if (!recommendedProductsContainer) {
            return;
        }

        let recommendedProducts = [];

        try {
            const response = await fetch('/api/products/recommended?limit=4');
            const data = await response.json();
            if (response.ok && data.success && Array.isArray(data.products) && data.products.length > 0) {
                recommendedProducts = data.products.map(product => ({
                    id: Number(product.id),
                    name: product.name,
                    price: Number(product.price || 0),
                    image: product.image,
                    rating: Number(product.rating || 0),
                    inStock: true
                }));
            }
        } catch (error) {
            console.warn('Failed to load recommended products from API, using fallback.');
        }

        if (recommendedProducts.length === 0) {
            recommendedProducts = [
                {
                    id: 1,
                    name: 'Featured Plant',
                    price: 25.00,
                    image: '/static/main/frontside/images/indoor/Dracaena_plants.jpg',
                    rating: 4.6,
                    inStock: true
                },
                {
                    id: 2,
                    name: 'Indoor Favorite',
                    price: 18.00,
                    image: '/static/main/frontside/images/indoor/ZZ_plants.jpg',
                    rating: 4.5,
                    inStock: true
                }
            ];
        }

        const productsHTML = recommendedProducts.map(product => `
            <div class="col-md-3 col-sm-6 mb-4">
                <div class="card h-100 border-0 shadow-sm recommended-product">
                    <img src="${product.image}" class="card-img-top" alt="${product.name}" style="height: 200px; object-fit: cover;">
                    <div class="card-body">
                        <h6 class="card-title">${product.name}</h6>
                        <div class="rating mb-2">
                            ${generateStarRating(product.rating)}
                            <small class="text-muted ms-1">(${product.rating.toFixed(1)})</small>
                        </div>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="h6 text-success mb-0">$${product.price.toFixed(2)}</span>
                            <button class="btn btn-outline-success btn-sm add-recommended-btn" data-product-id="${product.id}">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        recommendedProductsContainer.innerHTML = productsHTML;
        recommendedProductsContainer.dataset.bound = 'true';
        recommendedProductsContainer.onclick = (e) => {
            const button = e.target.closest('.add-recommended-btn');
            if (!button) {
                return;
            }
            const productId = Number(button.dataset.productId);
            const product = recommendedProducts.find(p => Number(p.id) === productId);
            if (product) {
                addRecommendedToCart(product);
            }
        };
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
        fetch('/add-to-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: Number(product.id),
                quantity: 1
            })
        })
        .then(response => response.json().then(data => ({ status: response.status, data })))
        .then(({ status, data }) => {
            if (status !== 200 || !data.success) {
                throw new Error(data.message || 'Unable to add product');
            }

            const existingItem = cartItems.find(item => normalizeProductId(item.id) === normalizeProductId(product.id));
            if (existingItem) {
                existingItem.quantity += 1;
            } else {
                cartItems.push({
                    id: Number(product.id),
                    name: product.name,
                    price: Number(product.price || 0),
                    image: product.image,
                    quantity: 1,
                    category: 'Plant',
                    inStock: true
                });
            }

            saveCartToStorage();
            displayCartItems();
            updateCartSummary();
            updateCartBadge();
            showMessage(`${product.name} added to cart!`, 'success');
        })
        .catch(error => {
            showMessage(error.message || 'Unable to add product', 'error');
        });
    }

    function updateCartBadge() {
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        if (cartBadge) {
            cartBadge.textContent = totalItems;
        }
    }

    function saveCartToStorage() {
        localStorage.setItem('cart', JSON.stringify(cartItems));
        if (appliedCoupon) {
            localStorage.setItem('appliedCoupon', appliedCoupon.code);
            localStorage.setItem('appliedCouponMeta', JSON.stringify(appliedCoupon));
        } else {
            localStorage.removeItem('appliedCoupon');
            localStorage.removeItem('appliedCouponMeta');
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
        // Check authentication before allowing add to cart
        fetch('/add-to-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: productData.id,
                name: productData.name,
                price: productData.price,
                quantity: 1
            })
        })
        .then(response => {
            if (response.status === 401) {
                // User not logged in, redirect to login
                return response.json().then(data => {
                    const loginUrl = data.redirect || '/login';
                    window.location.href = loginUrl;
                    throw new Error('Redirecting to login');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                // User is authenticated, add to cart
                const existingItem = cartItems.find(item => item.id === productData.id);
                
                if (existingItem) {
                    existingItem.quantity += 1;
                    showMessage(`${productData.name} quantity updated!`, 'success');
                } else {
                    cartItems.push({
                        ...productData,
                        quantity: 1,
                        inStock: true
                    });
                    showMessage(`${productData.name} added to cart!`, 'success');
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
            }
        })
        .catch(error => {
            if (!error.message.includes('Redirecting')) {
                showMessage('Error adding to cart. Please try again.', 'error');
            }
            return false;
        });
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
