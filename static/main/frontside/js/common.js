/**
 * Common Alert Handler
 * Shows success/error messages from URL parameters
 */
function showAlertFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const message = urlParams.get('message');
    const type = urlParams.get('type');
    
    if (message && typeof Swal !== 'undefined') {
        Swal.fire({
            title: type === 'success' ? 'Success!' : 'Error!',
            text: message,
            icon: type === 'success' ? 'success' : 'error',
            confirmButtonText: 'OK'
        });
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

/**
 * Image Preview Handler
 * Handles click, drag-drop, and file selection for image uploads
 */
function setupImagePreview(previewElementId, inputElementId) {
    const imagePreview = document.getElementById(previewElementId);
    const imageInput = document.getElementById(inputElementId);
    
    if (!imagePreview || !imageInput) return;

    // Click to upload
    imagePreview.addEventListener('click', function() {
        imageInput.click();
    });

    // Display preview when file is selected
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                imagePreview.innerHTML = '<img src="' + event.target.result + '" alt="Product Image">';
                imagePreview.classList.add('has-image');
            };
            reader.readAsDataURL(file);
        }
    });

    // Drag and drop functionality
    imagePreview.addEventListener('dragover', function(e) {
        e.preventDefault();
        imagePreview.style.borderColor = 'var(--primary-green)';
        imagePreview.style.backgroundColor = '#f0f8f5';
    });

    imagePreview.addEventListener('dragleave', function(e) {
        e.preventDefault();
        imagePreview.style.borderColor = 'var(--border-color)';
        imagePreview.style.backgroundColor = 'var(--bg-light)';
    });

    imagePreview.addEventListener('drop', function(e) {
        e.preventDefault();
        imagePreview.style.borderColor = 'var(--border-color)';
        imagePreview.style.backgroundColor = 'var(--bg-light)';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            imageInput.files = files;
            const event = new Event('change', { bubbles: true });
            imageInput.dispatchEvent(event);
        }
    });
}

/**
 * Generic Delete Confirmation
 * Shows SweetAlert confirmation before deleting
 * @param {event} event - Click event
 * @param {string} itemType - Type of item to delete (product, category, etc)
 * @param {string} itemId - ID of the item to delete
 * @param {string} route - Route prefix for delete (e.g., 'products', 'categories')
 */
function confirmDelete(event, itemType, itemId, route) {
    event.preventDefault();
    
    if (typeof Swal === 'undefined') {
        if (confirm(`Are you sure you want to delete this ${itemType}?`)) {
            window.location.href = `/${route}/delete/${itemId}`;
        }
        return;
    }
    
    Swal.fire({
        title: `Delete ${itemType}?`,
        text: `Are you sure? This ${itemType} will be permanently removed.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d32f2f',
        cancelButtonColor: '#9e9e9e',
        confirmButtonText: 'Yes, Delete',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = `/${route}/delete/${itemId}`;
        }
    });
}

// Initialize on page load
window.addEventListener('load', function() {
    showAlertFromUrl();
});
