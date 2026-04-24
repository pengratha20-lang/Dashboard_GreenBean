/**
 * Form Manager
 * Handles form state, autosave, and clearing on logout/session expiry
 */

class FormManager {
    constructor() {
        this.AUTOSAVE_INTERVAL = 5000; // Autosave every 5 seconds
        this.STORAGE_KEY_PREFIX = 'form_';
        this.autosaveIntervals = {};
        this.init();
    }
    
    /**
     * Initialize form manager
     */
    init() {
        // Setup form autosave functionality
        this.setupFormAutosave();
        
        // Listen for session cleanup events
        window.addEventListener('sessionCleanup', () => {
            this.clearAllForms();
        });
        
        console.log('✅ Form Manager initialized');
    }
    
    /**
     * Setup autosave for all forms with data-autosave attribute
     */
    setupFormAutosave() {
        const formsWithAutosave = document.querySelectorAll('form[data-autosave]');
        
        formsWithAutosave.forEach(form => {
            const formId = form.id || form.name || `form_${Math.random().toString(36).substr(2, 9)}`;
            
            // Restore previously saved data
            this.restoreFormData(form, formId);
            
            // Setup input listeners for autosave
            form.querySelectorAll('input, textarea, select').forEach(field => {
                field.addEventListener('change', () => {
                    this.autosaveFormData(form, formId);
                });
                
                field.addEventListener('blur', () => {
                    this.autosaveFormData(form, formId);
                });
            });
        });
    }
    
    /**
     * Get storage key for form
     */
    getStorageKey(formId) {
        return `${this.STORAGE_KEY_PREFIX}${formId}`;
    }
    
    /**
     * Auto-save form data to localStorage
     */
    autosaveFormData(form, formId) {
        const formData = new FormData(form);
        const data = {};
        
        // Extract form data (excluding file inputs)
        for (let [key, value] of formData.entries()) {
            if (key === 'csrf_token') continue; // Skip CSRF tokens
            
            if (data[key]) {
                // Handle multiple values with same name (checkboxes, multiple selects)
                if (!Array.isArray(data[key])) {
                    data[key] = [data[key]];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }
        
        try {
            localStorage.setItem(this.getStorageKey(formId), JSON.stringify({
                data: data,
                timestamp: Date.now(),
                formId: formId
            }));
            
            // Show quick save indicator if element exists
            this.showSaveIndicator(form);
        } catch (error) {
            console.warn('⚠️ Could not autosave form:', error);
        }
    }
    
    /**
     * Restore previously saved form data
     */
    restoreFormData(form, formId) {
        try {
            const storageKey = this.getStorageKey(formId);
            const savedData = localStorage.getItem(storageKey);
            
            if (!savedData) return;
            
            const { data, timestamp } = JSON.parse(savedData);
            
            // Only restore if saved less than 24 hours ago
            if (Date.now() - timestamp > 86400000) {
                localStorage.removeItem(storageKey);
                return;
            }
            
            // Restore each field
            for (let [key, value] of Object.entries(data)) {
                const field = form.querySelector(`[name="${key}"]`);
                if (field) {
                    if (field.type === 'checkbox') {
                        field.checked = value === field.value || value === 'on';
                    } else if (field.type === 'radio') {
                        const radio = form.querySelector(`[name="${key}"][value="${value}"]`);
                        if (radio) radio.checked = true;
                    } else {
                        field.value = value;
                    }
                }
            }
            
            console.log(`✅ Restored form data for ${formId}`);
        } catch (error) {
            console.warn('⚠️ Could not restore form data:', error);
        }
    }
    
    /**
     * Show save indicator on form
     */
    showSaveIndicator(form) {
        let indicator = form.querySelector('.form-save-indicator');
        
        if (!indicator) {
            indicator = document.createElement('small');
            indicator.className = 'form-save-indicator text-success ms-2';
            indicator.style.display = 'none';
            form.querySelector('.form-title') || form.querySelector('h1')?.after(indicator);
            if (!form.querySelector('.form-title')) {
                form.insertAdjacentElement('afterbegin', indicator);
            }
        }
        
        indicator.style.display = 'inline';
        indicator.textContent = '💾 Saved';
        
        clearTimeout(indicator.hideTimeout);
        indicator.hideTimeout = setTimeout(() => {
            indicator.style.display = 'none';
        }, 2000);
    }
    
    /**
     * Clear specific form data and form itself
     */
    clearForm(form) {
        const formId = form.id || form.name || `form_${Math.random().toString(36).substr(2, 9)}`;
        
        // Clear localStorage
        localStorage.removeItem(this.getStorageKey(formId));
        
        // Reset form fields
        form.reset();
        
        // Clear image previews if present
        form.querySelectorAll('.image-preview').forEach(preview => {
            preview.innerHTML = `
                <div class="image-preview-placeholder">
                    <i class="fas fa-image"></i>
                    <p>Click to upload or drag and drop</p>
                </div>
            `;
            preview.classList.remove('has-image');
        });
        
        // Clear file inputs
        form.querySelectorAll('input[type="file"]').forEach(input => {
            input.value = '';
        });
        
        console.log(`✅ Cleared form: ${formId}`);
    }
    
    /**
     * Clear all forms (called on logout/session expiry)
     */
    clearAllForms() {
        // Clear all localStorage form data
        const keysToDelete = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith(this.STORAGE_KEY_PREFIX)) {
                keysToDelete.push(key);
            }
        }
        keysToDelete.forEach(key => localStorage.removeItem(key));
        
        // Reset all forms on page
        document.querySelectorAll('form').forEach(form => {
            this.clearForm(form);
        });
        
        console.log('✅ All forms cleared');
    }
    
    /**
     * Get form save status
     */
    getFormStatus(formId) {
        const storageKey = this.getStorageKey(formId);
        const savedData = localStorage.getItem(storageKey);
        
        if (savedData) {
            try {
                const { timestamp } = JSON.parse(savedData);
                const lastSaved = new Date(timestamp);
                return {
                    hasSavedData: true,
                    lastSaved: lastSaved,
                    age: Date.now() - timestamp
                };
            } catch (error) {
                return { hasSavedData: false };
            }
        }
        
        return { hasSavedData: false };
    }
}

// Initialize form manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.formManager = new FormManager();
    });
} else {
    window.formManager = new FormManager();
}

/**
 * Helper function to clear a specific form
 * Usage: clearFormById('productForm')
 */
function clearFormById(formId) {
    const form = document.getElementById(formId);
    if (form && window.formManager) {
        window.formManager.clearForm(form);
    }
}

/**
 * Helper function to check form save status
 * Usage: getFormStatus('productForm')
 */
function getFormStatus(formId) {
    if (window.formManager) {
        return window.formManager.getFormStatus(formId);
    }
    return { hasSavedData: false };
}
