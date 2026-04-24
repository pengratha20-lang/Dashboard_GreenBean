/**
 * Enhanced Add-to-Cart Handler
 * Multiple fallback methods to ensure reliability
 * 1. Axios (if available)
 * 2. Fetch API (modern browsers)
 * 3. Form submission (JavaScript disabled fallback)
 */

class AddToCartHandler {
    constructor() {
        this.button = document.getElementById('add-to-cart');
        this.quantityInput = document.getElementById('quantity');
        this.useAxios = typeof axios !== 'undefined';
        this.isProcessing = false;  // ✅ Flag to prevent double clicks
        this.init();
    }

    init() {
        if (!this.button) {
            console.error('Add to cart button not found');
            return;
        }

        // Attach click handler
        this.button.addEventListener('click', (e) => this.handleAddToCart(e));
        
        // Also support Enter key on quantity input
        this.quantityInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleAddToCart(e);
            }
        });

        console.log('✅ Add-to-Cart handler initialized');
    }

    handleAddToCart(e) {
        e.preventDefault();
        
        // ✅ Prevent double clicks
        if (this.isProcessing) {
            console.warn('⚠️ Request already in progress');
            return;
        }
        
        // Get quantity and validate
        const quantity = this.validateQuantity();
        if (!quantity) return;

        // Get product data
        const productData = this.getProductData();
        if (!productData) return;
        
        // Also sync quantity to hidden form (for fallback)
        const hiddenQtyInput = document.getElementById('form-quantity');
        if (hiddenQtyInput) {
            hiddenQtyInput.value = quantity;
        }

        // Mark as processing
        this.isProcessing = true;

        // Disable button during processing
        this.setButtonState('processing');

        // Try adding to cart
        if (this.useAxios) {
            this.addToCartWithAxios(productData, quantity);
        } else {
            this.addToCartWithFetch(productData, quantity);
        }
    }

    validateQuantity() {
        let quantity = parseInt(this.quantityInput.value) || 1;

        // Validate input
        if (quantity < 1) {
            this.showError('Please enter a quantity of at least 1');
            this.quantityInput.value = 1;
            return null;
        }

        if (quantity > 10) {
            this.showError('Maximum quantity is 10 items per order');
            this.quantityInput.value = 10;
            return null;
        }

        return quantity;
    }

    getProductData() {
        try {
            return {
                id: this.button.getAttribute('data-product-id'),
                name: this.button.getAttribute('data-product-name'),
                price: parseFloat(this.button.getAttribute('data-product-price')),
                image: this.button.getAttribute('data-product-image')
            };
        } catch (error) {
            console.error('Error getting product data:', error);
            this.showError('Product information not found');
            return null;
        }
    }

    /**
     * Method 1: Axios (Best for error handling)
     */
    addToCartWithAxios(productData, quantity) {
        axios.post('/add-to-cart', {
            id: productData.id,
            name: productData.name,
            price: productData.price,
            quantity: quantity
        })
        .then(response => {
            this.handleSuccess(response.data, productData, quantity);
        })
        .catch(error => {
            if (error.response && error.response.status === 401) {
                const data = error.response.data;
                window.location.href = data.redirect || '/login';
                return;
            }
            this.handleError(error, 'axios');
        });
    }

    /**
     * Method 2: Fetch API (Standard modern approach)
     */
    addToCartWithFetch(productData, quantity) {
        fetch('/add-to-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: productData.id,
                name: productData.name,
                price: productData.price,
                quantity: quantity
            })
        })
        .then(response => {
            // Handle redirect (e.g., to login)
            if (response.status === 401) {
                return response.json().then(data => {
                    window.location.href = data.redirect || '/login';
                });
            }
            return response.json().then(data => ({
                status: response.status,
                data: data
            }));
        })
        .then(result => {
            if (result.status === 200 || result.status === 201) {
                this.handleSuccess(result.data, productData, quantity);
            } else {
                this.handleApiError(result.data);
            }
        })
        .catch(error => {
            this.handleError(error, 'fetch');
        });
    }

    handleSuccess(response, productData, quantity) {
        console.log('✅ Item added to cart via Flask:', response);

        // ✅ Show success message with product name (like shop page)
        const message = `<i class="fas fa-check-circle me-2"></i>${productData.name} added to cart (x${quantity})`;
        this.showSuccess(message);

        // Update cart badge
        const cartBadge = document.getElementById('cart-badge');
        if (cartBadge && response.cart_count) {
            cartBadge.textContent = response.cart_count;
        }

        // Show button confirmation
        this.setButtonState('success');

        // Reset after 2 seconds
        setTimeout(() => {
            this.setButtonState('idle');
            this.isProcessing = false;  // ✅ Reset processing flag
        }, 2000);
    }

    setButtonState(state) {
        switch(state) {
            case 'processing':
                this.button.disabled = true;
                this.button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding...';
                this.button.classList.add('btn-secondary');
                this.button.classList.remove('btn-success');
                break;

            case 'success':
                this.button.disabled = true;
                this.button.innerHTML = '<i class="fas fa-check me-2"></i>Added to Cart!';
                this.button.classList.add('btn-success');
                this.button.classList.remove('btn-secondary');
                break;

            case 'error':
                this.button.disabled = false;
                this.button.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>Error - Try Again';
                this.button.classList.add('btn-danger');
                this.button.classList.remove('btn-success', 'btn-secondary');
                break;

            case 'idle':
            default:
                this.button.disabled = false;
                this.button.innerHTML = '<i class="fas fa-shopping-cart me-2"></i>Add to Cart';
                this.button.classList.add('btn-success');
                this.button.classList.remove('btn-secondary', 'btn-danger');
                break;
        }
    }

    handleError(error, method) {
        console.error(`❌ Error adding to cart (${method}):`, error);
        this.isProcessing = false;  // ✅ Reset processing flag on error
        this.showError('Failed to add item to cart. Please try again.');
        this.setButtonState('error');
        
        setTimeout(() => {
            this.setButtonState('idle');
        }, 2000);
    }

    handleApiError(response) {
        console.error('❌ API Error:', response);
        this.isProcessing = false;  // ✅ Reset processing flag on error
        this.showError(response.message || 'Failed to add item to cart');
        this.setButtonState('error');
        
        setTimeout(() => {
            this.setButtonState('idle');
        }, 2000);
    }

    handleError(error, method) {
        console.error(`❌ Error adding to cart (${method}):`, error);
        this.isProcessing = false;  // ✅ Reset processing flag on error
        this.showError('Failed to add item to cart. Please try again.');
        this.setButtonState('error');
        
        setTimeout(() => {
            this.setButtonState('idle');
        }, 2000);
    }

    handleApiError(response) {
        console.error('❌ API Error:', response);
        this.isProcessing = false;  // ✅ Reset processing flag on error
        this.showError(response.message || 'Failed to add item to cart');
        this.setButtonState('error');
        
        setTimeout(() => {
            this.setButtonState('idle');
        }, 2000);
    }

    showSuccess(message) {
        if (typeof showSiteAlert === 'function') {
            showSiteAlert('success', message);
        } else {
            alert(message);
        }
    }

    showError(message) {
        if (typeof showSiteAlert === 'function') {
            showSiteAlert('error', message);
        } else {
            alert('Error: ' + message);
        }
    }

    updateCartBadge(cart) {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        const cartBadge = document.getElementById('cart-badge');
        if (cartBadge) {
            cartBadge.textContent = totalItems;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.addToCartHandler = new AddToCartHandler();
});
