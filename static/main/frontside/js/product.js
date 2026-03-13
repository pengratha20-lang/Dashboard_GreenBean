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
    }

    function addToCart(button) {
        const productData = {
            id: button.dataset.productId,
            name: button.dataset.productName,
            price: parseFloat(button.dataset.productPrice),
            image: button.dataset.productImage
        };
        
        const existingItem = cartItems.find(item => item.id === productData.id);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cartItems.push({ ...productData, quantity: 1 });
        }
        
        // Save to localStorage
        saveCartToLocalStorage();
        
        updateCartDisplay();
        showCartNotification(productData.name);
        
        // Add visual feedback
        button.classList.add('added');
        button.innerHTML = '<i class="fas fa-check me-1"></i>Added!';
        
        setTimeout(() => {
            button.classList.remove('added');
            button.innerHTML = '<i class="fas fa-cart-plus me-1"></i>Add to Cart';
        }, 2000);
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

    // Initialize cart
    updateCartDisplay();

    // Update cart count and total price
    function updateCartDisplay() {
        const totalItems = cartItems.reduce((sum, item) => sum + item.quantity, 0);
        cartCountElement.textContent = totalItems;
        
        let totalPrice = 0;
        cartItemsList.innerHTML = '';
        
        cartItems.forEach((item, index) => {
            totalPrice += item.price * item.quantity;
            const listItem = createCartItemElement(item, index);
            cartItemsList.appendChild(listItem);
        });
        
        totalPriceElement.textContent = totalPrice.toFixed(2);
        
        // Show/hide checkout button based on cart contents
        if (checkoutBtn) {
            checkoutBtn.style.display = cartItems.length > 0 ? 'block' : 'none';
        }
    }

    // Create cart item element
    function createCartItemElement(item, index) {
        const listItem = document.createElement('li');
        listItem.className = 'cart-item fade-in-up';
        listItem.innerHTML = `
            <img src="${item.image}" alt="${item.name}" class="cart-img">
            <div class="cart-item-details">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-price">$${item.price.toFixed(2)}</div>
            </div>
            <div class="quantity-control">
                <button class="qty-btn decrease-qty" data-index="${index}" aria-label="Decrease quantity">−</button>
                <input type="number" value="${item.quantity}" readonly class="qty-input" min="1">
                <button class="qty-btn increase-qty" data-index="${index}" aria-label="Increase quantity">+</button>
            </div>
            <button class="remove-item-btn" data-index="${index}" aria-label="Remove item">
                <i class="fas fa-trash"></i>
            </button>
        `;
        return listItem;
    }

    // Add to cart functionality
    function addToCart(productData) {
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
                // User is authenticated, add to cart
                const existingItemIndex = cartItems.findIndex(item => item.id === productData.id);
                
                if (existingItemIndex !== -1) {
                    cartItems[existingItemIndex].quantity += 1;
                    showNotification(`${productData.name} quantity updated!`, 'success');
                } else {
                    cartItems.push({
                        ...productData,
                        quantity: 1
                    });
                    showNotification(`${productData.name} added to cart!`, 'success');
                }
                
                updateCartDisplay();
                animateCartIcon();
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            showNotification('Error adding to cart. Please try again.', 'error');
        });
    }

    // Animate cart icon when item is added
    function animateCartIcon() {
        if (cartIcon) {
            cartIcon.style.transform = 'scale(1.2)';
            setTimeout(() => {
                cartIcon.style.transform = 'scale(1)';
            }, 200);
        }
    }

    // Show notification
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
        `;
        
        // Add styles
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            backgroundColor: type === 'success' ? '#28a745' : '#17a2b8',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '8px',
            zIndex: '9999',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Event Listeners

    // Add to cart buttons
    document.addEventListener('click', (event) => {
        if (event.target.closest('.add-to-cart-btn')) {
            const button = event.target.closest('.add-to-cart-btn');
            const productData = {
                id: button.getAttribute('data-product-id'),
                name: button.getAttribute('data-product-name'),
                price: parseFloat(button.getAttribute('data-product-price')),
                image: button.getAttribute('data-product-image')
            };
            
            addToCart(productData);
        }
    });

    // Cart icon click
    if (cartIcon) {
        cartIcon.addEventListener('click', (e) => {
            e.preventDefault();
            cartModal.classList.add('open');
            cartModal.classList.add('slide-in-right');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        });
    }

    // Close cart modal
    function closeCart() {
        cartModal.classList.remove('open');
        cartModal.classList.remove('slide-in-right');
        document.body.style.overflow = 'auto'; // Restore scrolling
    }

    if (closeCartBtn) {
        closeCartBtn.addEventListener('click', closeCart);
    }

    // Close cart when clicking outside
    cartModal.addEventListener('click', (e) => {
        if (e.target === cartModal) {
            closeCart();
        }
    });

    // Quantity controls and remove item
    cartItemsList.addEventListener('click', (event) => {
        const index = parseInt(event.target.getAttribute('data-index'));
        
        if (event.target.classList.contains('increase-qty')) {
            cartItems[index].quantity += 1;
            updateCartDisplay();
        } else if (event.target.classList.contains('decrease-qty')) {
            if (cartItems[index].quantity > 1) {
                cartItems[index].quantity -= 1;
            } else {
                cartItems.splice(index, 1);
                showNotification('Item removed from cart', 'info');
            }
            updateCartDisplay();
        } else if (event.target.closest('.remove-item-btn')) {
            const itemName = cartItems[index].name;
            cartItems.splice(index, 1);
            updateCartDisplay();
            showNotification(`${itemName} removed from cart`, 'info');
        }
    });

    // Clear cart
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', () => {
            if (cartItems.length > 0) {
                if (confirm('Are you sure you want to clear your cart?')) {
                    cartItems.length = 0;
                    updateCartDisplay();
                    showNotification('Cart cleared', 'info');
                }
            }
        });
    }

    // Checkout functionality
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => {
            if (cartItems.length > 0) {
                const total = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
                alert(`Checkout - Total: $${total.toFixed(2)}\n\nThis is a demo. In a real application, this would redirect to a payment page.`);
                closeCart();
            }
        });
    }

    // Search functionality
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = searchInput.value.toLowerCase().trim();
                const productCards = document.querySelectorAll('.product-card');
                
                productCards.forEach(card => {
                    const productName = card.querySelector('.product-title').textContent.toLowerCase();
                    const productDescription = card.querySelector('.product-description').textContent.toLowerCase();
                    
                    const matchesSearch = productName.includes(query) || productDescription.includes(query);
                    
                    if (matchesSearch || query === '') {
                        card.style.display = 'block';
                        card.parentElement.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                        card.parentElement.style.display = 'none';
                    }
                });
                
                // Show/hide "no results" message
                const visibleProducts = document.querySelectorAll('.product-card[style*="display: block"], .product-card:not([style*="display: none"])').length;
                
                let noResultsMsg = document.getElementById('no-results-message');
                if (visibleProducts === 0 && query !== '') {
                    if (!noResultsMsg) {
                        noResultsMsg = document.createElement('div');
                        noResultsMsg.id = 'no-results-message';
                        noResultsMsg.className = 'text-center py-5';
                        noResultsMsg.innerHTML = `
                            <i class="fas fa-search fa-3x text-muted mb-3"></i>
                            <h4 class="text-muted">No products found</h4>
                            <p class="text-muted">Try adjusting your search terms</p>
                        `;
                        document.getElementById('products-container').appendChild(noResultsMsg);
                    }
                    noResultsMsg.style.display = 'block';
                } else if (noResultsMsg) {
                    noResultsMsg.style.display = 'none';
                }
            }, 300); // Debounce search
        });
    }

    // Category filter functionality
    const categoryItems = document.querySelectorAll('.dropdown-item[data-category]');
    categoryItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const category = item.getAttribute('data-category');
            const productCards = document.querySelectorAll('.product-card');
            
            productCards.forEach(card => {
                const cardCategory = card.getAttribute('data-category');
                
                if (category === 'all' || cardCategory === category) {
                    card.style.display = 'block';
                    card.parentElement.style.display = 'block';
                } else {
                    card.style.display = 'none';
                    card.parentElement.style.display = 'none';
                }
            });
            
            // Update dropdown button text
            const dropdownButton = document.getElementById('categoryDropdown');
            if (dropdownButton) {
                dropdownButton.innerHTML = `<i class="fas fa-filter me-2"></i>${item.textContent}`;
            }
        });
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Lazy loading for images (if needed)
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Add fade-in animation to elements when they come into view
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    }, observerOptions);

    // Observe product cards
    document.querySelectorAll('.product-card').forEach(card => {
        observer.observe(card);
    });

    // Keyboard navigation for cart modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && cartModal.classList.contains('open')) {
            closeCart();
        }
    });

    console.log('Green Bean Shop initialized successfully!');
;
