/**
 * Bulk Operations Manager - Handle bulk delete, update, and export
 */

class BulkOperationsManager {
    constructor(tableSelector = 'table') {
        this.table = document.querySelector(tableSelector);
        this.checkboxes = [];
        this.selectedIds = new Set();
        this.init();
    }

    init() {
        // Find all checkboxes
        this.checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"][data-item-id]'));
        
        // Setup event listeners
        this.setupCheckboxListeners();
        this.updateBulkActionsUI();
    }

    setupCheckboxListeners() {
        // Individual checkbox listeners
        this.checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateSelectedItems());
        });

        // Select/Deselect all
        const selectAllBtn = document.querySelector('[data-action="select-all"]');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAll());
        }

        const deselectAllBtn = document.querySelector('[data-action="deselect-all"]');
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAll());
        }

        // Bulk delete
        const bulkDeleteBtn = document.querySelector('[data-action="bulk-delete"]');
        if (bulkDeleteBtn) {
            bulkDeleteBtn.addEventListener('click', () => this.bulkDelete());
        }

        // Bulk update status
        const statusSelect = document.querySelector('[data-action="bulk-update-status"]');
        if (statusSelect) {
            statusSelect.addEventListener('change', (e) => this.bulkUpdateStatus(e.target.value));
        }

        // Export
        const exportBtn = document.querySelector('[data-action="export"]');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportData());
        }
    }

    updateSelectedItems() {
        this.selectedIds.clear();
        this.checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                this.selectedIds.add(checkbox.getAttribute('data-item-id'));
            }
        });
        this.updateBulkActionsUI();
    }

    updateBulkActionsUI() {
        const count = this.selectedIds.size;
        const bulkActionsBar = document.querySelector('.bulk-actions-bar');
        
        if (bulkActionsBar) {
            if (count > 0) {
                bulkActionsBar.classList.remove('d-none');
                bulkActionsBar.querySelector('[data-count]').textContent = count;
            } else {
                bulkActionsBar.classList.add('d-none');
            }
        }

        // Disable buttons if nothing selected
        const bulkDeleteBtn = document.querySelector('[data-action="bulk-delete"]');
        if (bulkDeleteBtn) {
            bulkDeleteBtn.disabled = count === 0;
        }
    }

    selectAll() {
        this.checkboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
        this.updateSelectedItems();
    }

    deselectAll() {
        this.checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateSelectedItems();
    }

    async bulkDelete() {
        if (this.selectedIds.size === 0) {
            alert('Please select items to delete');
            return;
        }

        const count = this.selectedIds.size;
        if (!confirm(`Are you sure you want to delete ${count} item(s)? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch('/admin/products/bulk-delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ ids: Array.from(this.selectedIds) })
            });

            const data = await response.json();

            if (data.success) {
                alert(`Successfully deleted ${data.deleted_count} item(s)`);
                location.reload();
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Bulk delete error:', error);
            alert('An error occurred while deleting items');
        }
    }

    async bulkUpdateStatus(newStatus) {
        if (this.selectedIds.size === 0) {
            alert('Please select items to update');
            return;
        }

        try {
            const response = await fetch('/admin/products/bulk-update-status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ 
                    ids: Array.from(this.selectedIds),
                    status: newStatus
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(data.message);
                location.reload();
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Bulk update error:', error);
            alert('An error occurred while updating items');
        }
    }

    exportData() {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/admin/products/export';
        
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = this.getCSRFToken();
        form.appendChild(csrfInput);

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    }

    getCSRFToken() {
        return document.querySelector('input[name="csrf_token"]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
               '';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const bulkManager = new BulkOperationsManager();
    window.bulkOperationsManager = bulkManager;
});

window.BulkOperationsManager = BulkOperationsManager;
