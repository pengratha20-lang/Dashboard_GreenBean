/**
 * Dashboard Form Handler - Improved error display and loading states
 */

class FormHandler {
    constructor(formSelector) {
        this.form = document.querySelector(formSelector);
        this.submitBtn = this.form?.querySelector('button[type="submit"]');
        this.originalBtnText = this.submitBtn?.textContent || 'Submit';
        this.init();
    }

    init() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    }

    handleSubmit(e) {
        // Clear previous errors
        this.clearErrors();

        // Show loading state
        this.setLoading(true);
    }

    setLoading(loading) {
        if (!this.submitBtn) return;
        
        if (loading) {
            this.submitBtn.disabled = true;
            this.submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm mr-2"></span>Processing...';
            this.submitBtn.classList.add('loading');
        } else {
            this.submitBtn.disabled = false;
            this.submitBtn.textContent = this.originalBtnText;
            this.submitBtn.classList.remove('loading');
        }
    }

    clearErrors() {
        // Remove all error messages and highlights
        document.querySelectorAll('.form-error-message').forEach(el => el.remove());
        document.querySelectorAll('.form-group.has-error').forEach(el => {
            el.classList.remove('has-error');
        });
        document.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
    }

    showError(fieldName, message) {
        const field = this.form?.querySelector(`[name="${fieldName}"]`);
        if (!field) return;

        // Mark field as invalid
        field.classList.add('is-invalid');

        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error-message invalid-feedback d-block';
        errorDiv.textContent = message;

        // Insert after field
        field.parentNode.insertBefore(errorDiv, field.nextSibling);

        // Highlight form group
        field.closest('.form-group')?.classList.add('has-error');
    }

    showErrors(errorsObject) {
        Object.keys(errorsObject).forEach(field => {
            this.showError(field, errorsObject[field]);
        });
    }

    showFriendlyError(errorInfo) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.role = 'alert';
        
        let html = `<strong>${errorInfo.title || 'Error'}</strong><br>${errorInfo.message}`;
        if (errorInfo.suggestion) {
            html += `<br><small class="text-muted">${errorInfo.suggestion}</small>`;
        }
        
        alertDiv.innerHTML = html + `
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        this.form?.insertAdjacentElement('beforebegin', alertDiv);
    }

    isLoading() {
        return this.submitBtn?.classList.contains('loading') || false;
    }
}

// Export for use in templates
window.FormHandler = FormHandler;
