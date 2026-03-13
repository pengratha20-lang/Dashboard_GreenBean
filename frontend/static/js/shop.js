document.addEventListener("DOMContentLoaded", () => {
    // Global variables
    const cartItems = [];
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
    
    // Test if JS is loading properly
    console.log('Shop.js loaded successfully. Cart items:', cartItems.length);

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
        // Clear filters (support both id and any sidebar buttons with class)
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

    function handleCartActions(e) {
        if (e.target.classList.contains('add-to-cart-btn') || e.target.closest('.add-to-cart-btn')) {
            e.preventDefault();
            e.stopPropagation(); // Prevent event bubbling to parent elements
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
    }

    function addToCart(button) {
        console.log('Add to cart button clicked:', button); // Debug log
        console.log('Button dataset:', button.dataset); // Debug log
        
        const productData = {
            id: button.dataset.productId,
            name: button.dataset.productName,
            price: parseFloat(button.dataset.productPrice),
            image: button.dataset.productImage,
            category: button.dataset.productCategory,
            description: button.dataset.productDescription || `Premium quality ${button.dataset.productName} for your home or garden.`,
            inStock: true
        };
        
        console.log('Product data extracted:', productData); // Debug log
        
        // Validate product data
        if (!productData.id || !productData.name || !productData.price || !productData.image) {
            console.error('Missing product data:', productData);
            alert('Error: Product data is incomplete. Please refresh and try again.');
            return;
        }
        
        // First, check authentication by sending to backend
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
                });
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                // User is authenticated, add to cart locally
                // Get cart from localStorage
                let cart = JSON.parse(localStorage.getItem('cart')) || [];
                
                const existingItem = cart.find(item => item.id === productData.id);
                
                if (existingItem) {
                    existingItem.quantity += 1;
                } else {
                    cart.push({ ...productData, quantity: 1 });
                }
                
                // Save to localStorage
                localStorage.setItem('cart', JSON.stringify(cart));
                
                // Update local cartItems array
                cartItems.length = 0;
                cartItems.push(...cart);
                
                updateCartDisplay();
                showCartNotification(productData.name);
                
                // Dispatch custom event for other pages to listen
                window.dispatchEvent(new CustomEvent('cartUpdated', { 
                    detail: { cart: cart, totalItems: cart.reduce((sum, item) => sum + item.quantity, 0) }
                }));
                
                // Add visual feedback
                button.classList.add('added');
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="fas fa-check me-1"></i>Added!';
                button.disabled = true;
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
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            alert('Error adding to cart. Please try again.');
        });
        
        // Success notification will be shown by showCartNotification function
    }

    function removeFromCart(index) {
        // Remove from localStorage
        let cart = JSON.parse(localStorage.getItem('cart')) || [];
        cart.splice(index, 1);
        localStorage.setItem('cart', JSON.stringify(cart));
        
        // Update local cartItems array
        cartItems.splice(index, 1);
        updateCartDisplay();
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('cartUpdated', { 
            detail: { cart: cart, totalItems: cart.reduce((sum, item) => sum + item.quantity, 0) }
        }));
    }

    function clearCart() {
        cartItems.length = 0;
        localStorage.removeItem('cart');
        updateCartDisplay();
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('cartUpdated', { 
            detail: { cart: [], totalItems: 0 }
        }));
    }

    function updateCartDisplay() {
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        const totalPrice = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        
        // Update cart count
        if (cartCountElement) cartCountElement.textContent = totalItems;
        if (sidebarCartCount) sidebarCartCount.textContent = totalItems;
        
        // Update cart badge (multiple possible elements)
        const cartBadges = document.querySelectorAll('#cart-badge, .cart-badge');
        cartBadges.forEach(badge => {
            if (badge) badge.textContent = totalItems;
        });
        
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
        
        // Force badge visibility update
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
        console.log('Showing notification for:', productName); // Debug log
        
        // Remove any existing notifications first
        const existingNotifications = document.querySelectorAll('.cart-notification');
        existingNotifications.forEach(n => n.remove());
        
        // Create a simple, reliable notification
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
        
        // Add CSS animation keyframe if not exists
        if (!document.querySelector('#cart-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'cart-notification-styles';
            style.textContent = `
                @keyframes fadeInRight {
                    from {
                        opacity: 0;
                        transform: translateX(100px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                @keyframes fadeOutRight {
                    from {
                        opacity: 1;
                        transform: translateX(0);
                    }
                    to {
                        opacity: 0;
                        transform: translateX(100px);
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        console.log('Bootstrap-style notification added to DOM'); // Debug log
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            if (notification && notification.parentNode) {
                const alert = notification.querySelector('.alert');
                if (alert) {
                    alert.style.animation = 'fadeOutRight 0.5s ease';
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.remove();
                            console.log('Notification removed'); // Debug log
                        }
                    }, 500);
                }
            }
        }, 4000);
        
        // Animate cart badge
        const cartBadges = document.querySelectorAll('#cart-badge, .cart-badge');
        cartBadges.forEach(badge => {
            if (badge) {
                badge.style.transform = 'scale(1.2)';
                badge.style.transition = 'transform 0.3s ease';
                setTimeout(() => {
                    badge.style.transform = 'scale(1)';
                }, 300);
            }
        });
        
        // Play a subtle success sound (optional)
        try {
            // Create a simple success sound
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsgBSl+1Oq3d');
            audio.volume = 0.3;
            audio.play().catch(() => {}); // Ignore errors if audio doesn't work
        } catch (e) {
            // Ignore audio errors
        }
    }

    function handleSearch() {
        // Just trigger applyFilters which handles search now
        applyFilters();
    }

    function setInitialCategoryFilter(category) {
        const allowedCategories = new Set(['all', 'indoor', 'outdoor', 'pot', 'accessories']);
        const selected = allowedCategories.has(category) ? category : 'all';
        const targetFilter = document.querySelector(`input[name="categoryFilter"][value="${selected}"]`);
        const allFilter = document.getElementById('all-category');

        if (targetFilter) {
            targetFilter.checked = true;
        } else if (allFilter) {
            allFilter.checked = true;
        }
    }

    function applyFilters() {
        // ALWAYS start completely fresh - reset all products to original state
        let filtered = [...allProducts]; 
        
        // Clear any existing filter states
        allProducts.forEach(product => {
            product.classList.remove('filtered-hidden');
            product.style.display = 'block'; // Reset to visible first
        });
        
        // Search filter first
        const query = (searchInput?.value || navbarSearch?.value || '').toLowerCase().trim();
        if (query) {
            filtered = filtered.filter(product => {
                const name = product.dataset.name?.toLowerCase() || '';
                const category = product.dataset.category?.toLowerCase() || '';
                return name.includes(query) || category.includes(query);
            });
        }
        
        // Category filter
        const selectedCategory = document.querySelector('input[name="categoryFilter"]:checked')?.value;
        if (selectedCategory && selectedCategory !== 'all') {
            filtered = filtered.filter(product => {
                const productCategory = (product.dataset.category || '').toLowerCase().trim();
                const targetCategory = selectedCategory.toLowerCase().trim();
                return productCategory === targetCategory;
            });
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
        } else if ((priceMinInput?.value && priceMinInput.value.trim() !== '') || (priceMaxInput?.value && priceMaxInput.value.trim() !== '')) {
            // Only apply manual price range if values are actually set
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
        // Clear existing filters first
        clearAllFilters();
        
        // Filter products based on special attributes
        let filtered = [...allProducts];
        
        switch(filterType) {
            case 'featured':
            case 'popular':
                filtered = filtered.filter(product => product.dataset.popular === 'true');
                break;
            case 'new':
                filtered = filtered.filter(product => product.dataset.new === 'true');
                break;
            case 'sale':
                filtered = filtered.filter(product => product.dataset.sale === 'true');
                break;
            case 'rating':
                filtered = filtered.filter(product => {
                    const rating = parseInt(product.dataset.rating || 0);
                    return rating >= 5; // Show 5-star products
                });
                break;
            default:
                // For any other filter, just show all
                break;
        }
        
        // Highlight the active quick link
        document.querySelectorAll('.quick-link-btn').forEach(btn => {
            btn.classList.remove('active', 'bg-success', 'text-white');
        });
        const activeBtn = document.querySelector(`.quick-link-btn[data-filter="${filterType}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active', 'bg-success', 'text-white');
        }
        
        displayProducts(filtered);
    }

    function displayProducts(products) {
        // FIRST: Reset ALL products to hidden state and clear all classes
        allProducts.forEach(product => {
            product.style.display = 'none';
            product.classList.add('filtered-hidden');
            // Reset load more state for fresh filtering
            if (product.classList.contains('extra-product')) {
                product.classList.add('d-none');
            }
        });
        
        // SECOND: Show only the filtered products (limit to first 9 initially)
        products.forEach((product, index) => {
            product.style.display = 'block';
            product.classList.remove('filtered-hidden');
            
            // Show first 9 products, hide the rest for load more functionality
            if (index < 9) {
                if (product.classList.contains('extra-product')) {
                    product.classList.remove('d-none');
                }
            } else {
                // Hide products beyond first 9 for load more
                if (product.classList.contains('extra-product')) {
                    product.classList.add('d-none');
                }
            }
        });
        
        // Show/hide no results message
        if (noResultsDiv) {
            if (products.length === 0) {
                noResultsDiv.classList.remove('d-none');
            } else {
                noResultsDiv.classList.add('d-none');
            }
        }
        
        // Update product count display
        updateProductCount(products.length);
        
        // Handle load more button visibility
        const loadMoreBtn = document.getElementById('load-more-btn');
        const loadMoreSection = document.getElementById('load-more-section');
        if (loadMoreBtn && loadMoreSection) {
            // Only show load more if there are more than 9 products AND some are hidden
            if (products.length > 9) {
                const hiddenProducts = products.filter((product, index) => 
                    index >= 9 && product.classList.contains('extra-product')
                );
                
                if (hiddenProducts.length > 0) {
                    loadMoreSection.style.display = 'block';
                    loadMoreBtn.style.display = 'block';
                    loadMoreBtn.disabled = false;
                    loadMoreBtn.classList.remove('btn-secondary');
                    loadMoreBtn.classList.add('btn-outline-success');
                    loadMoreBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Load More Products';
                } else {
                    loadMoreSection.style.display = 'none';
                }
            } else {
                // Hide load more if 9 or fewer products
                loadMoreSection.style.display = 'none';
            }
        }
    }

    function resetLoadMore() {
        // For filtered results, hide extra products that were previously shown
        const extraProducts = document.querySelectorAll('.product-item.extra-product');
        extraProducts.forEach(product => {
            // Only hide if it's currently visible due to filtering
            if (!product.classList.contains('filtered-hidden') && product.style.display !== 'none') {
                product.classList.add('d-none');
            }
        });
        
        // Show load more button ONLY if there are more than 9 visible products after filtering
        const loadMoreBtn = document.getElementById('load-more-btn');
        const loadMoreSection = document.getElementById('load-more-section');
        if (loadMoreBtn && loadMoreSection) {
            // Count total visible products after filtering
            const visibleProducts = Array.from(allProducts).filter(p => 
                !p.classList.contains('filtered-hidden') && p.style.display !== 'none'
            );
            
            // Count how many are currently hidden due to load-more (extra products)
            const hiddenExtraProducts = Array.from(extraProducts).filter(p => 
                !p.classList.contains('filtered-hidden') && p.classList.contains('d-none')
            );
            
            // Only show load more if there are more than 9 total visible products AND there are hidden extra products
            if (visibleProducts.length > 9 && hiddenExtraProducts.length > 0) {
                loadMoreSection.style.display = 'block';
                loadMoreBtn.style.display = 'block';
                loadMoreBtn.disabled = false;
                loadMoreBtn.classList.remove('btn-secondary');
                loadMoreBtn.classList.add('btn-outline-success');
                loadMoreBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Load More Products';
            } else {
                loadMoreSection.style.display = 'none';
            }
        }
    }

    function updateProductCount(count) {
        // Keep sidebar category badges static (server-rendered global totals).
        const resultsCountElement = document.getElementById('results-count');
        if (resultsCountElement) {
            resultsCountElement.textContent = count;
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
        // Find hidden products that match current filters
        const loadMoreBtn = document.getElementById('load-more-btn');
        const hiddenProducts = Array.from(allProducts).filter(product => 
            !product.classList.contains('filtered-hidden') && // Passes current filters
            product.style.display !== 'none' && // Not filtered out
            product.classList.contains('extra-product') && // Is an extra product
            product.classList.contains('d-none') // Currently hidden by load-more
        );
        
        if (!loadMoreBtn || hiddenProducts.length === 0) {
            if (loadMoreBtn) loadMoreBtn.style.display = 'none';
            return;
        }

        // Disable button and show loading state
        loadMoreBtn.disabled = true;
        loadMoreBtn.classList.add('btn-secondary');
        loadMoreBtn.classList.remove('btn-outline-success');
        loadMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';

        setTimeout(() => {
            // Show next batch (up to 6 items)
            const batch = hiddenProducts.slice(0, 6);
            batch.forEach(el => {
                el.classList.remove('d-none');
            });

            // Check if there are still more hidden products
            const stillHidden = Array.from(allProducts).filter(product => 
                !product.classList.contains('filtered-hidden') &&
                product.style.display !== 'none' &&
                product.classList.contains('extra-product') &&
                product.classList.contains('d-none')
            );
            
            if (stillHidden.length === 0) {
                loadMoreBtn.style.display = 'none';
            } else {
                loadMoreBtn.disabled = false;
                loadMoreBtn.classList.remove('btn-secondary');
                loadMoreBtn.classList.add('btn-outline-success');
                loadMoreBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Load More Products';
            }
        }, 500);
    }

    function clearAllFilters() {
        // Reset category filter to "All"
        const allCategoryFilter = document.getElementById('all-category');
        if (allCategoryFilter) {
            allCategoryFilter.checked = true;
        }
        
        // Reset price range filters
        priceRangeFilters.forEach(filter => {
            filter.checked = false;
        });
        
        // Reset price inputs
        if (priceMinInput) priceMinInput.value = '';
        if (priceMaxInput) priceMaxInput.value = '';
        
        // Reset search
        if (searchInput) searchInput.value = '';
        if (navbarSearch) navbarSearch.value = '';
        
        // Reset all products to original state
        allProducts.forEach(product => {
            product.style.display = 'block';
            product.classList.remove('filtered-hidden');
            // Reset load more state to original
            if (product.classList.contains('extra-product')) {
                product.classList.add('d-none');
            }
        });
        
        // Hide no results message
        if (noResultsDiv) {
            noResultsDiv.classList.add('d-none');
        }
        
        // Reset load more button
        const loadMoreBtn = document.getElementById('load-more-btn');
        const loadMoreSection = document.getElementById('load-more-section');
        if (loadMoreBtn && loadMoreSection) {
            const hiddenProducts = document.querySelectorAll('.product-item.extra-product.d-none');
            if (hiddenProducts.length > 0) {
                loadMoreSection.style.display = 'block';
                loadMoreBtn.style.display = 'block';
                loadMoreBtn.disabled = false;
                loadMoreBtn.classList.remove('btn-secondary');
                loadMoreBtn.classList.add('btn-outline-success');
                loadMoreBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Load More Products';
            }
        }
        
        // Update product count to total
        updateProductCount(allProducts.length);
        
        // Clear quick link highlighting
        document.querySelectorAll('.quick-link-btn').forEach(btn => {
            btn.classList.remove('active', 'bg-success', 'text-white');
        });
    }

    function handleCheckout() {
        if (cartItems.length === 0) {
            alert('Your cart is empty!');
            return;
        }
        
        // Simulate checkout process
        alert(`Proceeding to checkout with ${cartItems.length} items. Total: $${cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0).toFixed(2)}`);
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
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
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
    function initializeProductCards() {
        console.log('Initializing product cards...');
        
        // Make cards clickable by extracting product ID and creating URL
        const productItems = document.querySelectorAll('.product-item');
        console.log('Found product items:', productItems.length);
        
        productItems.forEach((item, index) => {
            const card = item.querySelector('.card');
            if (card) {
                card.classList.add('clickable-card');
                card.style.cursor = 'pointer';
                
                // Extract product ID from existing links or create from index
                let productId = index + 1;
                const existingLink = card.querySelector('a[href*="/product/"]');
                if (existingLink) {
                    const match = existingLink.href.match(/\/product\/(\d+)/);
                    if (match) productId = match[1];
                }
                
                card.setAttribute('data-product-url', `/product/${productId}`);
                
                // Add click handler
                card.addEventListener('click', function(e) {
                    // Don't navigate if clicking on buttons or interactive elements
                    if (e.target.closest('button') || e.target.closest('a') || e.target.closest('.add-to-cart-btn')) {
                        return;
                    }
                    const url = this.getAttribute('data-product-url');
                    if (url) {
                        window.location.href = url;
                    }
                });
                
                // Add text truncation classes
                const title = item.querySelector('.card-title');
                if (title) {
                    title.classList.add('text-truncate');
                    title.style.maxWidth = '200px';
                }
                
                const description = item.querySelector('.card-text');
                if (description) {
                    description.classList.add('text-truncate-2-lines');
                }
            }
        });
        
        console.log('Product cards initialized successfully');
    }
    
    // Expose functions for debugging
    window.shopDebug = {
        cartItems: cartItems,
        addToCart: addToCart,
        loadMoreProducts: loadMoreProducts,
        showCartNotification: showCartNotification
    };
    
    console.log('Shop.js fully loaded. Debug functions available via window.shopDebug');
});
