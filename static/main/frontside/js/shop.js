document.addEventListener("DOMContentLoaded", () => {
    // Global variables
    const cartItems = [];
    let filteredProducts = [];
    
    // Cart elements
    const cartCountElement = document.getElementById('cart-badge') || document.getElementById('cart-count');
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
    const shopContent = document.getElementById('shop-content');
    const initialCategoryFilter = (shopContent?.dataset.categoryFilter || 'all').toLowerCase().trim();

    // Initialize
    loadCartFromStorage();
    updateCartDisplay();
    initializeEventListeners();
    initializeProductCards();
    setInitialCategoryFilter(initialCategoryFilter);
    
    // Initialize filters - make sure all products are visible initially
    applyFilters();

    function loadCartFromStorage() {
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        cartItems.length = 0;
        cartItems.push(...cart);
    }

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
            filter.addEventListener('change', () => {
                // Clear manual price inputs when selecting radio button
                if (priceMinInput) priceMinInput.value = '';
                if (priceMaxInput) priceMaxInput.value = '';
                applyFilters();
            });
        });
        
        // Price range inputs - clear radio buttons when typing
        if (priceMinInput && priceMaxInput) {
            priceMinInput.addEventListener('input', () => {
                // Clear price range radio buttons when typing custom values
                priceRangeFilters.forEach(filter => filter.checked = false);
                applyFilters();
            });
            priceMaxInput.addEventListener('input', () => {
                // Clear price range radio buttons when typing custom values
                priceRangeFilters.forEach(filter => filter.checked = false);
                applyFilters();
            });
        }
        
        // Sort functionality
        const sortMenu = document.querySelector('[aria-labelledby="sortDropdown"]');
        if (sortMenu) {
            sortMenu.addEventListener('click', handleSort);
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
        const clearBtns = document.querySelectorAll('.clear-filters-btn');
        clearBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                clearAllFilters();
                // close sidebar on mobile if open
                const sidebar = document.querySelector('.sidebar-area');
                if (sidebar && sidebar.classList.contains('show')) sidebar.classList.remove('show');
            });
        });
        
        // Quick Links functionality
        const quickLinkBtns = document.querySelectorAll('.quick-link-btn');
        quickLinkBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                handleQuickLinkFilter(btn.dataset.filter);
            });
        });
        
        // Mobile filter button
        const mobileFilterBtn = document.getElementById('mobile-filter-btn');
        if (mobileFilterBtn) {
            mobileFilterBtn.addEventListener('click', toggleSidebar);
        }
    }

    function handleCartActions(e) {        // Cart Actions
        if (e.target.classList.contains('add-to-cart-btn') || e.target.closest('.add-to-cart-btn')) {
            e.preventDefault();
            e.stopPropagation();
            const button = e.target.classList.contains('add-to-cart-btn') ? e.target : e.target.closest('.add-to-cart-btn');
            addToCart(button);
        }
        
        if (e.target.classList.contains('cart-item-remove')) {
            e.preventDefault();
            e.stopPropagation();
            const index = parseInt(e.target.dataset.index);
            removeFromCart(index);
        }
        
        if (e.target.id === 'checkout-btn') {
            e.preventDefault();
            e.stopPropagation();
            handleCheckout();
        }
        
        if (e.target.id === 'clear-cart-btn' || e.target.closest('#clear-cart-btn')) {
            e.preventDefault();
            e.stopPropagation();
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

    function addToCart(button) {
        const productData = {
            id: button.dataset.productId,
            name: button.dataset.productName,
            price: parseFloat(button.dataset.productPrice),
            image: button.dataset.productImage,
            category: button.dataset.productCategory,
            description: button.dataset.productDescription || `Premium quality ${button.dataset.productName} for your home or garden.`,
            inStock: true
        };
        
        if (!productData.id || !productData.name || !productData.price || !productData.image) {
            showShopErrorNotification('Error: Product data is incomplete. Please refresh and try again.');
            return;
        }
        
        // Show loading state
        const originalHTML = button.innerHTML;
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
            // Handle login required (401)
            if (status === 401 || data.requiresLogin) {
                button.disabled = false;
                button.innerHTML = originalHTML;
                showShopErrorNotification(data.message || 'Please log in to add items to your cart');
                setTimeout(() => {
                    const loginUrl = data.redirect || '/login';
                    window.location.href = loginUrl;
                }, 1500);
                return;
            }
            
            if (status === 200 || status === 201) {
                // Success
                if (data && data.success) {
                    let cart = JSON.parse(localStorage.getItem('cart')) || [];
                    const existingItem = cart.find(item => item.id === productData.id);
                    if (existingItem) {
                        existingItem.quantity += 1;
                    } else {
                        cart.push({ ...productData, quantity: 1 });
                    }
                    localStorage.setItem('cart', JSON.stringify(cart));
                    cartItems.length = 0;
                    cartItems.push(...cart);
                    
                    updateCartDisplay();
                    showCartNotification(productData.name);
                    
                    window.dispatchEvent(new CustomEvent('cartUpdated', { 
                        detail: { cart: cart, totalItems: cart.reduce((sum, item) => sum + item.quantity, 0) }
                    }));
                    
                    button.classList.add('added');
                    button.innerHTML = '<i class="fas fa-check me-1"></i>Added!';
                    button.style.backgroundColor = '#28a745';
                    button.style.borderColor = '#28a745';
                    
                    setTimeout(() => {
                        button.classList.remove('added');
                        button.innerHTML = originalHTML;
                        button.disabled = false;
                        button.style.backgroundColor = '';
                        button.style.borderColor = '';
                    }, 1500);
                }
            } else {
                // Error - show user-friendly message
                showShopErrorNotification(data.message || 'Error adding to cart. Please try again.');
                button.disabled = false;
                button.innerHTML = originalHTML;
            }
        })
        .catch(error => {
            showShopErrorNotification('Error adding to cart. Please try again.');
            button.disabled = false;
            button.innerHTML = originalHTML;
        });
    }
    
    function showShopErrorNotification(message) {
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
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        })
        .then(response => {
            if (response.status === 401) {
                return response.json().then(data => {
                    const loginUrl = data.redirect || '/login';
                    window.location.href = loginUrl;
                });
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                showWishlistNotification(productData.product_name, 'Added to your wishlist successfully!', 'info');
                const icon = button.querySelector('i');
                if (icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas', 'text-danger');
                }
                button.classList.add('in-wishlist');
            } else if (data && !data.success) {
                // Show 'Already in wishlist' notification
                showWishlistNotification(productData.product_name, data.message || 'Already in your wishlist!', 'info');
                button.disabled = false;
                
                // If already in wishlist, make the heart red anyway
                const icon = button.querySelector('i');
                if (icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas', 'text-danger');
                }
            }
        })
        .catch(error => {
            showWishlistNotification('Error', 'Could not add to wishlist. Please try again.', 'danger');
            button.disabled = false;
        });
    }

    function showWishlistNotification(title, message, type = 'danger') {
        const notification = document.createElement('div');
        notification.className = 'wishlist-notification';
        
        // Map type to icon and color
        let iconClass = 'fa-heart';
        let alertClass = 'alert-light';
        if (type === 'info') {
            iconClass = 'fa-info-circle';
            alertClass = 'alert-success';
        } else if (type === 'danger') {
            iconClass = 'fa-exclamation-circle';
            alertClass = 'alert-danger';
        }
        
        notification.innerHTML = `
            <div class="alert ${alertClass} shadow-lg" style="
                position: fixed;
                top: 100px;
                right: 20px;
                z-index: 9999;
                min-width: 320px;
                animation: fadeInRight 0.5s ease;
                border: none;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15) !important;
                background: white;
            ">
                <div class="d-flex align-items-center">
                    <div class="bg-light p-2 rounded-circle me-3">
                        <i class="fas ${iconClass} ${type === 'danger' ? 'text-danger' : 'text-success'}" style="font-size: 1.5rem;"></i>
                    </div>
                    <div style="flex: 1;">
                        <div class="fw-bold text-dark">${title}</div>
                        <div class="small text-muted">${message}</div>
                    </div>
                    <button type="button" class="btn-close ms-2" onclick="this.closest('.wishlist-notification').remove()"></button>
                </div>
            </div>
        `;
        document.body.appendChild(notification);
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.style.animation = 'fadeOutRight 0.5s ease forwards';
                setTimeout(() => notification.remove(), 500);
            }
        }, 4000);
    }

    function removeFromCart(index) {
        let cart = JSON.parse(localStorage.getItem('cart')) || [];
        cart.splice(index, 1);
        localStorage.setItem('cart', JSON.stringify(cart));
        
        cartItems.splice(index, 1);
        updateCartDisplay();
        
        window.dispatchEvent(new CustomEvent('cartUpdated', { 
            detail: { cart: cart, totalItems: cart.reduce((sum, item) => sum + item.quantity, 0) }
        }));
    }

    function clearCart() {
        cartItems.length = 0;
        localStorage.removeItem('cart');
        updateCartDisplay();
        
        window.dispatchEvent(new CustomEvent('cartUpdated', { 
            detail: { cart: [], totalItems: 0 }
        }));
    }

    function updateCartDisplay() {
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        const totalPrice = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        
        if (cartCountElement) cartCountElement.textContent = totalItems;
        if (sidebarCartCount) sidebarCartCount.textContent = totalItems;
        
        const cartBadges = document.querySelectorAll('#cart-badge, .cart-badge');
        cartBadges.forEach(badge => {
            if (badge) badge.textContent = totalItems;
        });
        
        updateSidebarCart();
        
        if (cartTotalSection) {
            if (totalItems > 0) {
                cartTotalSection.classList.remove('d-none');
                if (sidebarCartTotal) sidebarCartTotal.textContent = `$${totalPrice.toFixed(2)}`;
            } else {
                cartTotalSection.classList.add('d-none');
            }
        }
        
        cartBadges.forEach(badge => {
            if (badge) {
                badge.style.display = totalItems > 0 ? 'inline' : 'inline';
                badge.textContent = totalItems;
            }
        });
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
        const existingNotifications = document.querySelectorAll('.cart-notification');
        existingNotifications.forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = 'cart-notification';
        notification.innerHTML = `
            <div class="alert alert-success shadow-lg" style="
                position: fixed;
                top: 120px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                animation: fadeInRight 0.5s ease;
                border: none;
                box-shadow: 0 8px 25px rgba(0,0,0,0.2) !important;
            ">
                <div class="d-flex align-items-center">
                    <i class="fas fa-check-circle text-success me-3" style="font-size: 1.2rem;"></i>
                    <div>
                        <strong>${productName}</strong> added to cart!
                        <div class="small text-muted">View cart to checkout</div>
                    </div>
                    <button type="button" class="btn-close ms-auto" onclick="this.closest('.cart-notification').remove()"></button>
                </div>
            </div>
        `;
        
        if (!document.querySelector('#cart-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'cart-notification-styles';
            style.textContent = `
                @keyframes fadeInRight { from { opacity: 0; transform: translateX(100px); } to { opacity: 1; transform: translateX(0); } }
                @keyframes fadeOutRight { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(100px); } }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        setTimeout(() => {
            if (notification && notification.parentNode) {
                const alert = notification.querySelector('.alert');
                if (alert) {
                    alert.style.animation = 'fadeOutRight 0.5s ease';
                    setTimeout(() => { if (notification.parentNode) notification.remove(); }, 500);
                }
            }
        }, 4000);
    }

    function handleSearch() {
        applyFilters();
    }

    function setInitialCategoryFilter(category) {
        const allowedCategories = new Set(['all', 'indoor', 'outdoor', 'pot', 'accessories']);
        const selected = allowedCategories.has(category) ? category : 'all';
        const targetFilter = document.querySelector(`input[name="categoryFilter"][value="${selected}"]`);
        const allFilter = document.getElementById('all-category');

        if (targetFilter) targetFilter.checked = true;
        else if (allFilter) allFilter.checked = true;
    }

    function applyFilters() {
        let filtered = [...allProducts]; 
        allProducts.forEach(product => {
            product.classList.remove('filtered-hidden');
            product.style.display = 'block';
        });
        
        const query = (searchInput?.value || navbarSearch?.value || '').toLowerCase().trim();
        if (query) {
            filtered = filtered.filter(product => {
                const name = product.dataset.name?.toLowerCase() || '';
                const category = product.dataset.category?.toLowerCase() || '';
                return name.includes(query) || category.includes(query);
            });
        }
        
        const selectedCategory = document.querySelector('input[name="categoryFilter"]:checked')?.value;
        if (selectedCategory && selectedCategory !== 'all') {
            filtered = filtered.filter(product => (product.dataset.category || '').toLowerCase().trim() === selectedCategory.toLowerCase().trim());
        }
        
        const selectedPriceRange = document.querySelector('input[name="priceRange"]:checked')?.value;
        const minPrice = parseFloat(priceMinInput?.value || 0);
        const maxPrice = parseFloat(priceMaxInput?.value || 1000);
        
        if (selectedPriceRange) {
            const [min, max] = selectedPriceRange.split('-').map(Number);
            filtered = filtered.filter(product => {
                const price = parseFloat(product.dataset.price);
                return price >= min && price <= max;
            });
        } else if ((priceMinInput?.value && priceMinInput.value.trim() !== '') || (priceMaxInput?.value && priceMaxInput.value.trim() !== '')) {
            filtered = filtered.filter(product => {
                const price = parseFloat(product.dataset.price);
                const actualMin = priceMinInput?.value && priceMinInput.value.trim() !== '' ? minPrice : 0;
                const actualMax = priceMaxInput?.value && priceMaxInput.value.trim() !== '' ? maxPrice : 1000;
                return price >= actualMin && price <= actualMax;
            });
        }
        displayProducts(filtered);
    }

    function handleQuickLinkFilter(filterType) {
        clearAllFilters();
        let filtered = [...allProducts];
        
        // Use the new data-is-* attributes
        switch(filterType) {
            case 'featured': 
            case 'popular': 
                filtered = filtered.filter(product => {
                    const card = product.querySelector('.product-card');
                    return card && card.dataset.isPopular === 'true';
                }); 
                break;
            case 'new': 
                filtered = filtered.filter(product => {
                    const card = product.querySelector('.product-card');
                    return card && card.dataset.isNew === 'true';
                }); 
                break;
            case 'sale': 
                filtered = filtered.filter(product => {
                    const card = product.querySelector('.product-card');
                    return card && card.dataset.isSale === 'true';
                }); 
                break;
            case 'rating': 
                filtered = filtered.filter(product => {
                    const card = product.querySelector('.product-card');
                    return card && parseInt(card.dataset.rating || 0) >= 4;
                }); 
                break;
        }
        document.querySelectorAll('.quick-link-btn').forEach(btn => btn.classList.remove('active', 'bg-success', 'text-white'));
        const activeBtn = document.querySelector(`.quick-link-btn[data-filter="${filterType}"]`);
        if (activeBtn) activeBtn.classList.add('active', 'bg-success', 'text-white');
        displayProducts(filtered);
    }

    function displayProducts(products) {
        allProducts.forEach(product => {
            product.style.display = 'none';
            product.classList.add('filtered-hidden');
            if (product.classList.contains('extra-product')) product.classList.add('d-none');
        });
        
        products.forEach((product, index) => {
            product.style.display = 'block';
            product.classList.remove('filtered-hidden');
            if (index < 9) { if (product.classList.contains('extra-product')) product.classList.remove('d-none'); }
            else { if (product.classList.contains('extra-product')) product.classList.add('d-none'); }
        });
        
        if (noResultsDiv) {
            if (products.length === 0) noResultsDiv.classList.remove('d-none');
            else noResultsDiv.classList.add('d-none');
        }
        
        updateProductCount(products.length);
        
        const loadMoreBtn = document.getElementById('load-more-btn');
        const loadMoreSection = document.getElementById('load-more-section');
        if (loadMoreBtn && loadMoreSection) {
            if (products.length > 9) {
                const hiddenProducts = products.filter((product, index) => index >= 9 && product.classList.contains('extra-product'));
                if (hiddenProducts.length > 0) {
                    loadMoreSection.style.display = 'block';
                    loadMoreBtn.style.display = 'block';
                    loadMoreBtn.disabled = false;
                    loadMoreBtn.classList.remove('btn-secondary');
                    loadMoreBtn.classList.add('btn-outline-success');
                    loadMoreBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Load More Products';
                } else { loadMoreSection.style.display = 'none'; }
            } else { loadMoreSection.style.display = 'none'; }
        }
    }

    function updateProductCount(count) {
        const resultsCountElement = document.getElementById('results-count');
        if (resultsCountElement) resultsCountElement.textContent = count;
    }

    function handleSort(e) {
        if (!e.target.dataset.sort) return;
        const sortType = e.target.dataset.sort;
        const visibleProducts = Array.from(productsGrid.querySelectorAll('.product-item:not([style*="display: none"])'));
        visibleProducts.sort((a, b) => {
            switch (sortType) {
                case 'name': return a.dataset.name.localeCompare(b.dataset.name);
                case 'name-desc': return b.dataset.name.localeCompare(a.dataset.name);
                case 'price': return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
                case 'price-desc': return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
                default: return 0;
            }
        });
        visibleProducts.forEach(product => productsGrid.appendChild(product));
        sortDropdown.innerHTML = `<i class="fas fa-sort me-2"></i>${e.target.textContent}`;
    }

    function toggleSidebar() {
        const sidebar = document.querySelector('.sidebar-area');
        const overlay = document.querySelector('.sidebar-overlay') || createSidebarOverlay();
        if (window.innerWidth < 992) { sidebar.classList.toggle('show'); overlay.classList.toggle('show'); }
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
            productsGrid.classList.add('list-view');
            productCards.forEach(card => card.classList.add('list-view-card'));
        } else {
            productsGrid.classList.remove('list-view');
            productCards.forEach(card => card.classList.remove('list-view-card'));
        }
    }

    function loadMoreProducts() {
        const loadMoreBtn = document.getElementById('load-more-btn');
        const hiddenProducts = Array.from(allProducts).filter(product => !product.classList.contains('filtered-hidden') && product.style.display !== 'none' && product.classList.contains('extra-product') && product.classList.contains('d-none'));
        if (!loadMoreBtn || hiddenProducts.length === 0) { if (loadMoreBtn) loadMoreBtn.style.display = 'none'; return; }
        loadMoreBtn.disabled = true;
        loadMoreBtn.classList.add('btn-secondary');
        loadMoreBtn.classList.remove('btn-outline-success');
        loadMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';
        setTimeout(() => {
            const batch = hiddenProducts.slice(0, 6);
            batch.forEach(el => el.classList.remove('d-none'));
            const stillHidden = Array.from(allProducts).filter(product => !product.classList.contains('filtered-hidden') && product.style.display !== 'none' && product.classList.contains('extra-product') && product.classList.contains('d-none'));
            if (stillHidden.length === 0) loadMoreBtn.style.display = 'none';
            else {
                loadMoreBtn.disabled = false;
                loadMoreBtn.classList.remove('btn-secondary');
                loadMoreBtn.classList.add('btn-outline-success');
                loadMoreBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Load More Products';
            }
        }, 500);
    }

    function clearAllFilters() {
        const allCategoryFilter = document.getElementById('all-category');
        if (allCategoryFilter) allCategoryFilter.checked = true;
        priceRangeFilters.forEach(filter => filter.checked = false);
        if (priceMinInput) priceMinInput.value = '';
        if (priceMaxInput) priceMaxInput.value = '';
        if (searchInput) searchInput.value = '';
        if (navbarSearch) navbarSearch.value = '';
        allProducts.forEach(product => {
            product.style.display = 'block';
            product.classList.remove('filtered-hidden');
            if (product.classList.contains('extra-product')) product.classList.add('d-none');
        });
        if (noResultsDiv) noResultsDiv.classList.add('d-none');
        updateProductCount(allProducts.length);
        document.querySelectorAll('.quick-link-btn').forEach(btn => btn.classList.remove('active', 'bg-success', 'text-white'));
    }

    function handleCheckout() {
        if (cartItems.length === 0) {
            showSiteAlert('warning', 'Your cart is empty.');
            return;
        }
        window.location.href = '/checkout';
    }

    function initializeProductCards() {
        const productItems = document.querySelectorAll('.product-item');
        productItems.forEach((item, index) => {
            const card = item.querySelector('.card');
            if (card) {
                card.classList.add('clickable-card');
                card.style.cursor = 'pointer';
                let productId = item.dataset.productId || (index + 1);
                card.setAttribute('data-product-url', `/product/${productId}`);
                card.addEventListener('click', function(e) {
                    if (e.target.closest('button') || e.target.closest('a') || e.target.closest('.add-to-cart-btn') || e.target.closest('.add-to-wishlist-btn')) return;
                    const url = this.getAttribute('data-product-url');
                    if (url) window.location.href = url;
                });
            }
        });
    }
});
