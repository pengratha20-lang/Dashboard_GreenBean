document.addEventListener("DOMContentLoaded", () => {
    // Global variables - Load cart from localStorage
    let cartItems = JSON.parse(localStorage.getItem('cart')) || [];
    let filteredProducts = [];
    
    // Cart elements
    const cartCountElement = document.getElementById('cart-count');
    const sidebarCartCount = document.getElementById('sidebar-cart-count');
    const sidebarCartItems = document.getElementById('sidebar-cart-items');
    const sidebarCartTotal = document.getElementById('sidebar-cart-total');
    const cartTotalSection = document.getElementById('cart-total-section');
    const cartToggleBtn = document.getElementById('cart-toggle-btn');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    
    // Search and filter elements
    const searchInput = document.getElementById('search-input');
    const navbarSearch = document.getElementById('navbar-search');
    const productsGrid = document.getElementById('products-grid');
    const categoryFilters = document.querySelectorAll('input[name="categoryFilter"]');
    const priceRangeFilters = document.querySelectorAll('input[name="priceRange"]');
    const priceMinInput = document.getElementById('price-min');
    const priceMaxInput = document.getElementById('price-max');
    const sortDropdown = document.getElementById('sortDropdown');
    const noResultsDiv = document.getElementById('no-results');
    
    // Get all product items
    const allProducts = Array.from(document.querySelectorAll('.product-item'));
    filteredProducts = [...allProducts];

    // Helper function to sync cart to localStorage
    function saveCartToLocalStorage() {
        localStorage.setItem('cart', JSON.stringify(cartItems));
    }

    // Initialize
    updateCartDisplay();
    initializeEventListeners();

    function initializeEventListeners() {
        // Cart functionality
        document.addEventListener('click', handleCartActions);
        
        // Search functionality
        if (searchInput) {
            searchInput.addEventListener('input', handleSearch);
        }
        if (navbarSearch) {
            navbarSearch.addEventListener('input', handleSearch);
        }
        
        // Filter functionality
        categoryFilters.forEach(filter => {
            filter.addEventListener('change', applyFilters);
        });
        
        priceRangeFilters.forEach(filter => {
            filter.addEventListener('change', applyFilters);
        });
        
        if (priceMinInput && priceMaxInput) {
            priceMinInput.addEventListener('input', applyFilters);
            priceMaxInput.addEventListener('input', applyFilters);
        }
        
        // Sort functionality
        if (sortDropdown) {
            sortDropdown.addEventListener('click', handleSort);
        }
        
        // Sidebar toggle for mobile
        if (sidebarToggleBtn) {
            sidebarToggleBtn.addEventListener('click', toggleSidebar);
        }
        
        // View toggle
        const viewToggle = document.querySelectorAll('input[name="view-toggle"]');
        viewToggle.forEach(toggle => {
            toggle.addEventListener('change', handleViewToggle);
        });
        
        // Load more functionality
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', loadMoreProducts);
        }
        
        // Clear filters
        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', clearAllFilters);
        }
        
        // Mobile filter button
        const mobileFilterBtn = document.getElementById('mobile-filter-btn');
        if (mobileFilterBtn) {
            mobileFilterBtn.addEventListener('click', toggleSidebar);
        }
    }

    function handleCartActions(e) {
        if (e.target.classList.contains('add-to-cart-btn') || e.target.closest('.add-to-cart-btn')) {
            e.preventDefault();
            const button = e.target.classList.contains('add-to-cart-btn') ? e.target : e.target.closest('.add-to-cart-btn');
            addToCart(button);
        }
        
        if (e.target.classList.contains('cart-item-remove')) {
            e.preventDefault();
            const index = parseInt(e.target.dataset.index);
            removeFromCart(index);
        }
        
        if (e.target.id === 'checkout-btn') {
            e.preventDefault();
            handleCheckout();
        }
        
        if (e.target.id === 'clear-cart-btn' || e.target.closest('#clear-cart-btn')) {
            e.preventDefault();
            clearCart();
        }

        // Wishlist Actions
        if (e.target.classList.contains('add-to-wishlist-btn') || e.target.closest('.add-to-wishlist-btn')) {
            e.preventDefault();
            e.stopPropagation();
            const button = e.target.classList.contains('add-to-wishlist-btn') ? e.target : e.target.closest('.add-to-wishlist-btn');
            addToWishlist(button);
        }
    }

    function addToWishlist(button) {
        const productData = {
            product_id: button.dataset.productId,
            product_name: button.dataset.productName,
            product_price: parseFloat(button.dataset.productPrice),
            product_image: button.dataset.productImage
        };
        
        button.disabled = true;
        
        fetch('/add-to-wishlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(productData)
        })
        .then(response => {
            if (response.status === 401) {
                return response.json().then(data => {
                    window.location.href = data.redirect || '/login';
                });
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                showWishlistNotification(productData.product_name);
                const icon = button.querySelector('i');
                if (icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas', 'text-danger');
                }
            } else if (data && !data.success) {
                showSiteAlert('error', data.message || 'Unable to add this item to your wishlist.');
                button.disabled = false;
            }
        })
        .catch(error => {
            showSiteAlert('error', 'Error adding to wishlist. Please try again.');
            button.disabled = false;
        });
    }

    function showWishlistNotification(productName) {
        const notification = document.createElement('div');
        notification.className = 'wishlist-notification';
        notification.innerHTML = `
            <div class="alert alert-danger shadow-lg" style="
                position: fixed;
                top: 100px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                animation: fadeInRight 0.5s ease;
                border: none;
                box-shadow: 0 8px 25px rgba(220, 53, 69, 0.2) !important;
            ">
                <div class="d-flex align-items-center">
                    <i class="fas fa-heart text-danger me-3" style="font-size: 1.2rem;"></i>
                    <div>
                        <strong>${productName}</strong> added to wishlist!
                        <div class="small text-muted">View wishlist in your profile</div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(notification);
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    function addToCart(button) {
        const productData = {
            id: button.dataset.productId,
            name: button.dataset.productName,
            price: parseFloat(button.dataset.productPrice),
            image: button.dataset.productImage
        };
        
        // Add loading state
        const origHtml = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Adding...';
        
        fetch('/add-to-cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: productData.id,
                name: productData.name,
                price: productData.price,
                quantity: 1
            })
        })
        .then(response => response.json().then(data => ({ status: response.status, data })))
        .then(({ status, data }) => {
            if (status === 200 || status === 201) {
                // Success
                if (data && data.success) {
                    const existingItem = cartItems.find(item => item.id === productData.id);
                    if (existingItem) {
                        existingItem.quantity += 1;
                    } else {
                        cartItems.push({ ...productData, quantity: 1 });
                    }
                    saveCartToLocalStorage();
                    updateCartDisplay();
                    showCartNotification(productData.name);
                    
                    button.classList.add('added');
                    button.innerHTML = '<i class="fas fa-check me-1"></i>Added!';
                    setTimeout(() => {
                        button.classList.remove('added');
                        button.disabled = false;
                        button.innerHTML = origHtml;
                    }, 2000);
                }
            } else {
                // Error - show user-friendly message
                showErrorNotification(data.message || 'Error adding to cart');
                button.disabled = false;
                button.innerHTML = origHtml;
            }
        })
        .catch(err => {
            showErrorNotification('Error adding to cart. Please try again.');
            button.disabled = false;
            button.innerHTML = origHtml;
        });
    }
    
    function showErrorNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-warning shadow-lg';
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: fadeInRight 0.5s ease;
            border: none;
            box-shadow: 0 8px 25px rgba(255, 193, 7, 0.2) !important;
        `;
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle text-warning me-3" style="font-size: 1.2rem;"></i>
                <div>
                    <strong>Alert</strong>
                    <div class="small">${message}</div>
                </div>
            </div>
        `;
        document.body.appendChild(notification);
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.remove();
            }
        }, 4000);
    }

    function removeFromCart(index) {
        cartItems.splice(index, 1);
        saveCartToLocalStorage();
        updateCartDisplay();
    }

    function clearCart() {
        cartItems.length = 0;
        saveCartToLocalStorage();
        updateCartDisplay();
    }

    function updateCartDisplay() {
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        const totalPrice = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        
        // Update cart count
        if (cartCountElement) cartCountElement.textContent = totalItems;
        if (sidebarCartCount) sidebarCartCount.textContent = totalItems;
        
        // Update cart badge
        const cartBadge = document.getElementById('cart-badge');
        if (cartBadge) cartBadge.textContent = totalItems;
        
        // Update sidebar cart
        updateSidebarCart();
        
        // Show/hide total section
        if (cartTotalSection) {
            if (totalItems > 0) {
                cartTotalSection.classList.remove('d-none');
                if (sidebarCartTotal) sidebarCartTotal.textContent = `$${totalPrice.toFixed(2)}`;
            } else {
                cartTotalSection.classList.add('d-none');
            }
        }
    }

    function updateSidebarCart() {
        if (!sidebarCartItems) return;
        
        if (cartItems.length === 0) {
            sidebarCartItems.innerHTML = `
                <div class="text-center py-4 text-muted">
                    <i class="fas fa-shopping-cart mb-2" style="font-size: 2rem; opacity: 0.3;"></i>
                    <p class="mb-0">Your cart is empty</p>
                </div>
            `;
            return;
        }
        
        sidebarCartItems.innerHTML = cartItems.map((item, index) => `
            <div class="cart-item">
                <img src="${item.image}" alt="${item.name}" class="cart-item-image">
                <div class="cart-item-details">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-price">$${item.price.toFixed(2)} x ${item.quantity}</div>
                </div>
                <button class="cart-item-remove" data-index="${index}" title="Remove item">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }

    function showCartNotification(productName) {
        // Create notification
        const notification = document.createElement('div');
        notification.className = 'cart-notification';
        notification.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show position-fixed" 
                 style="top: 100px; right: 20px; z-index: 1060; min-width: 300px;">
                <i class="fas fa-check-circle me-2"></i>
                <strong>${productName}</strong> added to cart!
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    function handleSearch() {
        const query = (searchInput?.value || navbarSearch?.value || '').toLowerCase().trim();
        
        filteredProducts = allProducts.filter(product => {
            const name = product.dataset.name?.toLowerCase() || '';
            const category = product.dataset.category?.toLowerCase() || '';
            return name.includes(query) || category.includes(query);
        });
        
        applyFilters();
    }

    function applyFilters() {
        let filtered = [...filteredProducts];
        
        // Category filter
        const selectedCategory = document.querySelector('input[name="categoryFilter"]:checked')?.value;
        if (selectedCategory && selectedCategory !== 'all') {
            filtered = filtered.filter(product => product.dataset.category === selectedCategory);
        }
        
        // Price range filter
        const selectedPriceRange = document.querySelector('input[name="priceRange"]:checked')?.value;
        const minPrice = parseFloat(priceMinInput?.value || 0);
        const maxPrice = parseFloat(priceMaxInput?.value || 1000);
        
        if (selectedPriceRange) {
            const [min, max] = selectedPriceRange.split('-').map(Number);
            filtered = filtered.filter(product => {
                const price = parseFloat(product.dataset.price);
                return price >= min && price <= max;
            });
        } else {
            filtered = filtered.filter(product => {
                const price = parseFloat(product.dataset.price);
                return price >= minPrice && price <= maxPrice;
            });
        }
        
        displayProducts(filtered);
    }

    function displayProducts(products) {
        // Hide all products
        allProducts.forEach(product => {
            product.style.display = 'none';
        });
        
        // Show filtered products
        products.forEach(product => {
            product.style.display = 'block';
        });
        
        // Show/hide no results message
        if (noResultsDiv) {
            if (products.length === 0) {
                noResultsDiv.classList.remove('d-none');
            } else {
                noResultsDiv.classList.add('d-none');
            }
        }
        
        // Update product count
        updateProductCount(products.length);
    }

    function updateProductCount(count) {
        // Update category badges
        const allCategoryBadge = document.querySelector('label[for="all-category"] .badge');
        if (allCategoryBadge) {
            allCategoryBadge.textContent = count;
        }
    }

    function handleSort(e) {
        if (!e.target.dataset.sort) return;
        
        const sortType = e.target.dataset.sort;
        const visibleProducts = Array.from(productsGrid.querySelectorAll('.product-item:not([style*="display: none"])'));
        
        visibleProducts.sort((a, b) => {
            switch (sortType) {
                case 'name':
                    return a.dataset.name.localeCompare(b.dataset.name);
                case 'name-desc':
                    return b.dataset.name.localeCompare(a.dataset.name);
                case 'price':
                    return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
                case 'price-desc':
                    return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
                default:
                    return 0;
            }
        });
        
        // Reorder DOM elements
        visibleProducts.forEach(product => {
            productsGrid.appendChild(product);
        });
        
        // Update dropdown text
        sortDropdown.innerHTML = `<i class="fas fa-sort me-2"></i>${e.target.textContent}`;
    }

    function toggleSidebar() {
        const sidebar = document.querySelector('.sidebar-area');
        const overlay = document.querySelector('.sidebar-overlay') || createSidebarOverlay();
        
        if (window.innerWidth < 992) {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        }
    }

    function createSidebarOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.addEventListener('click', toggleSidebar);
        document.body.appendChild(overlay);
        return overlay;
    }

    function handleViewToggle(e) {
        const isListView = e.target.id === 'list-view';
        const productCards = document.querySelectorAll('.product-card');
        
        if (isListView) {
            // Switch to list view
            productsGrid.classList.add('list-view');
            productCards.forEach(card => {
                card.classList.add('list-view-card');
            });
        } else {
            // Switch to grid view
            productsGrid.classList.remove('list-view');
            productCards.forEach(card => {
                card.classList.remove('list-view-card');
            });
        }
    }

    function loadMoreProducts() {
        // Simulate loading more products
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (loadMoreBtn) {
            loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
            
            setTimeout(() => {
                loadMoreBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Load More Products';
                // Here you would typically load more products from an API
            }, 1500);
        }
    }

    function clearAllFilters() {
        // Reset category filter
        const allCategoryFilter = document.getElementById('all-category');
        if (allCategoryFilter) {
            allCategoryFilter.checked = true;
        }
        
        // Reset price range filters
        priceRangeFilters.forEach(filter => {
            filter.checked = false;
        });
        
        // Reset price inputs
        if (priceMinInput) priceMinInput.value = 0;
        if (priceMaxInput) priceMaxInput.value = 50;
        
        // Reset search
        if (searchInput) searchInput.value = '';
        if (navbarSearch) navbarSearch.value = '';
        
        // Reset filtered products
        filteredProducts = [...allProducts];
        
        // Reapply filters (which will show all products)
        applyFilters();
    }

    function handleCheckout() {
        if (cartItems.length === 0) {
            showSiteAlert('warning', 'Your cart is empty.');
            return;
        }
        
        // Simulate checkout process
        showSiteAlert(
            'info',
            `Proceeding to checkout with ${cartItems.length} items. Total: $${cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0).toFixed(2)}`,
            { title: 'Checkout Preview' }
        );
    }

    // Navbar scroll effect
    let lastScrollTop = 0;
    const navbar = document.querySelector('.shop-header');
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            // Scrolling down
            navbar.style.transform = 'translateY(-100%)';
        } else {
            // Scrolling up
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = scrollTop;
    });

    // Add to cart animation
    const style = document.createElement('style');
    style.textContent = `
        .add-to-cart-btn.added {
            background-color: #28a745 !important;
            border-color: #28a745 !important;
            transform: scale(0.95);
        }
        
        .cart-notification {
            animation: slideInRight 0.3s ease;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .list-view .row {
            flex-direction: column !important;
        }
        
        .list-view-card {
            display: flex !important;
            flex-direction: row !important;
            max-width: 100% !important;
        }
        
        .list-view-card .card-img-top {
            width: 200px !important;
            height: 150px !important;
            object-fit: cover;
            flex-shrink: 0;
        }
        
        .list-view-card .card-body {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
    `;
    document.head.appendChild(style);
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
