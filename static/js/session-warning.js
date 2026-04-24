/**
 * Session Timeout Warning - Alert user before session expires
 */

class SessionWarningManager {
    constructor(checkIntervalSeconds = 30) {
        this.checkInterval = checkIntervalSeconds * 1000;
        this.warningShown = false;
        this.warningThresholdMinutes = 15;
        this.init();
    }

    init() {
        // Check session status periodically
        setInterval(() => this.checkSession(), this.checkInterval);
        
        // Check immediately
        this.checkSession();
    }

    async checkSession() {
        try {
            const response = await fetch('/api/session-info');
            if (!response.ok) return;

            const data = await response.json();
            
            if (data.is_expired) {
                this.handleSessionExpired();
            } else if (data.show_warning && !this.warningShown) {
                this.showWarning(data.remaining_minutes);
            }
        } catch (error) {
            console.log('Session check failed:', error);
        }
    }

    showWarning(remainingMinutes) {
        this.warningShown = true;

        const modal = document.createElement('div');
        modal.className = 'modal show';
        modal.id = 'session-warning-modal';
        modal.style.display = 'block';
        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('tabindex', '-1');

        const content = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-warning">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle"></i> Session Timeout Warning
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Your session will expire in <strong>${remainingMinutes} minute${remainingMinutes !== 1 ? 's' : ''}</strong>.</p>
                        <p>Click "Continue Session" to stay logged in, or you will be logged out automatically.</p>
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i> Your work is automatically saved, but you will need to log in again if the session expires.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            Continue Session
                        </button>
                        <a href="/admin/logout" class="btn btn-danger">
                            Logout Now
                        </a>
                    </div>
                </div>
            </div>
        `;

        modal.innerHTML = content;
        document.body.appendChild(modal);

        // Add event listeners
        const closeBtn = modal.querySelector('[data-bs-dismiss="modal"]');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.remove();
                this.warningShown = false;
            });
        }

        // Refresh session on continue
        const continueBtn = modal.querySelector('.btn-secondary');
        if (continueBtn) {
            continueBtn.addEventListener('click', async () => {
                await fetch('/api/refresh-session', { method: 'POST' });
                modal.remove();
                this.warningShown = false;
            });
        }
    }

    handleSessionExpired() {
        alert('Your session has expired. You will be logged out.');
        window.location.href = '/admin/logout';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if user is logged in (check for presence of logout link or admin panel)
    if (document.querySelector('[href*="/admin/logout"]') || document.querySelector('.admin-panel')) {
        new SessionWarningManager(30);
    }
});

window.SessionWarningManager = SessionWarningManager;
