/**
 * Session Manager
 * Handles session timeout warnings, auto-refresh, and graceful logout
 */

class SessionManager {
    constructor() {
        // Session duration: 1 hour (3600 seconds) or 7 days if "Remember Me"
        this.SESSION_DURATION = 3600; // seconds
        this.WARNING_TIME = 3000; // Show warning at 50 minutes (3000 seconds)
        this.CHECK_INTERVAL = 30000; // Check session every 30 seconds
        
        this.sessionStartTime = null;
        this.lastActivityTime = null;
        this.warningShown = false;
        this.isLoggedIn = false;
        this.sessionCheckInterval = null;
        
        this.init();
    }
    
    /**
     * Initialize session manager
     */
    init() {
        // Check if user is logged in
        this.checkLoginStatus();
        
        if (!this.isLoggedIn) return;
        
        // Set initial times
        this.sessionStartTime = Date.now();
        this.lastActivityTime = Date.now();
        
        // Create warning dialog element
        this.createWarningDialog();
        
        // Start monitoring user activity
        this.setupActivityListeners();
        
        // Start periodic session check
        this.startSessionCheck();
        
        console.log('✅ Session Manager initialized');
    }
    
    /**
     * Check if user is currently logged in
     */
    checkLoginStatus() {
        const userIdMeta = document.querySelector('meta[name="user-id"]');
        this.isLoggedIn = !!userIdMeta;
    }
    
    /**
     * Create warning dialog HTML
     */
    createWarningDialog() {
        if (document.getElementById('session-warning-modal')) return;
        
        const dialogHTML = `
            <div class="modal fade" id="session-warning-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div style="background: linear-gradient(135deg, #ff9800 0%, #e68900 100%); color: white; padding: 20px;">
                            <h5 class="modal-title fw-bold mb-0">
                                <i class="fas fa-hourglass-end me-2"></i>Session Expiring Soon
                            </h5>
                        </div>
                        <div class="modal-body p-4">
                            <p class="mb-3">Your session will expire in <strong><span id="session-countdown">10:00</span></strong> due to inactivity.</p>
                            <p class="text-muted mb-4">To continue working, click "Stay Logged In" or take any action on the page.</p>
                            <div class="alert alert-warning border-0 mb-0">
                                <i class="fas fa-info-circle me-2"></i>
                                <small>For security, inactive sessions are automatically logged out.</small>
                            </div>
                        </div>
                        <div class="modal-footer border-0">
                            <button type="button" class="btn btn-outline-secondary" onclick="sessionManager.logout()">
                                <i class="fas fa-sign-out-alt me-2"></i>Logout
                            </button>
                            <button type="button" class="btn btn-warning fw-bold" onclick="sessionManager.extendSession()">
                                <i class="fas fa-clock me-2"></i>Stay Logged In
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', dialogHTML);
    }
    
    /**
     * Setup activity listeners
     */
    setupActivityListeners() {
        const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
        
        events.forEach(event => {
            document.addEventListener(event, () => this.recordActivity(), { passive: true });
        });
    }
    
    /**
     * Record user activity and refresh session if needed
     */
    recordActivity() {
        this.lastActivityTime = Date.now();
        
        // Refresh session every 5 minutes of activity
        if ((this.lastActivityTime - this.sessionStartTime) % 300000 < 1000) {
            this.refreshSession();
        }
    }
    
    /**
     * Start periodic session check
     */
    startSessionCheck() {
        this.sessionCheckInterval = setInterval(() => {
            const timeElapsed = (Date.now() - this.sessionStartTime) / 1000; // in seconds
            const timeRemaining = this.SESSION_DURATION - timeElapsed;
            
            // Show warning at 50 minutes
            if (timeRemaining <= 600 && !this.warningShown) { // 600 seconds = 10 minutes
                this.warningShown = true;
                this.showWarningDialog(timeRemaining);
            }
            
            // Auto-logout when time is up
            if (timeRemaining <= 0) {
                this.handleSessionTimeout();
            }
            
            // Update countdown in modal if visible
            if (this.warningShown && document.getElementById('session-warning-modal')?.classList.contains('show')) {
                this.updateCountdown(timeRemaining);
            }
        }, 1000); // Check every second
    }
    
    /**
     * Show warning dialog
     */
    showWarningDialog(timeRemaining) {
        const modal = document.getElementById('session-warning-modal');
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            // Prevent closing by clicking outside
            modal.addEventListener('hide.bs.modal', (e) => {
                if (timeRemaining > 10) {
                    e.preventDefault();
                }
            });
        }
    }
    
    /**
     * Update countdown timer in modal
     */
    updateCountdown(seconds) {
        const countdownEl = document.getElementById('session-countdown');
        if (countdownEl && seconds > 0) {
            const minutes = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            countdownEl.textContent = `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    /**
     * Refresh session via AJAX
     */
    async refreshSession() {
        try {
            const response = await fetch('/refresh-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Reset session timer
                this.sessionStartTime = Date.now();
                this.warningShown = false;
                
                // Close warning modal if open
                const modal = document.getElementById('session-warning-modal');
                if (modal && modal.classList.contains('show')) {
                    bootstrap.Modal.getInstance(modal).hide();
                }
                
                console.log('✅ Session refreshed');
            } else if (response.status === 401) {
                this.handleSessionTimeout();
            }
        } catch (error) {
            console.error('❌ Session refresh error:', error);
        }
    }
    
    /**
     * Extend session from warning dialog
     */
    extendSession() {
        this.refreshSession();
        const modal = document.getElementById('session-warning-modal');
        if (modal && modal.classList.contains('show')) {
            bootstrap.Modal.getInstance(modal).hide();
        }
    }
    
    /**
     * Handle session timeout gracefully
     */
    async handleSessionTimeout() {
        clearInterval(this.sessionCheckInterval);
        
        // Perform comprehensive cleanup
        this.performSessionCleanup();
        
        // Hide warning modal
        const modal = document.getElementById('session-warning-modal');
        if (modal && modal.classList.contains('show')) {
            bootstrap.Modal.getInstance(modal).hide();
        }
        
        // Show timeout message
        const timeoutHTML = `
            <div class="modal fade" id="session-expired-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 20px;">
                            <h5 class="modal-title fw-bold mb-0">
                                <i class="fas fa-times-circle me-2"></i>Session Expired
                            </h5>
                        </div>
                        <div class="modal-body p-4">
                            <p class="mb-0">Your session has expired due to inactivity. Please login again to continue.</p>
                        </div>
                        <div class="modal-footer border-0">
                            <a href="/login" class="btn btn-danger fw-bold">
                                <i class="fas fa-sign-in-alt me-2"></i>Login Again
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', timeoutHTML);
        const expiredModal = new bootstrap.Modal(document.getElementById('session-expired-modal'));
        expiredModal.show();
        
        // Redirect after 3 seconds
        setTimeout(() => {
            window.location.href = '/login?message=Your+session+has+expired.+Please+login+again.&type=warning';
        }, 3000);
    }
    
    /**
     * Clear all form data stored in session/local storage
     */
    clearFormData() {
        // Clear localStorage for product forms
        const formStorageKeys = Object.keys(localStorage).filter(key => 
            key.includes('product') || 
            key.includes('form') || 
            key.includes('add-item') ||
            key.includes('edit-')
        );
        
        formStorageKeys.forEach(key => {
            localStorage.removeItem(key);
        });
        
        // Clear sessionStorage
        const sessionStorageKeys = Object.keys(sessionStorage).filter(key =>
            key.includes('form') || 
            key.includes('product') || 
            key.includes('cart') ||
            key.includes('add-item')
        );
        
        sessionStorageKeys.forEach(key => {
            sessionStorage.removeItem(key);
        });
        
        // Clear all form inputs if on dashboard
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.reset();
        });
        
        console.log('✅ Form data cleared');
    }
    
    /**
     * Clear image previews from forms
     */
    clearImagePreviews() {
        const imagePreviews = document.querySelectorAll('.image-preview');
        imagePreviews.forEach(preview => {
            preview.innerHTML = `
                <div class="image-preview-placeholder">
                    <i class="fas fa-image"></i>
                    <p>Click to upload or drag and drop</p>
                </div>
            `;
            preview.classList.remove('has-image');
        });
        
        const imageInputs = document.querySelectorAll('input[type="file"][name*="image"]');
        imageInputs.forEach(input => {
            input.value = '';
        });
        
        console.log('✅ Image previews cleared');
    }
    
    /**
     * Handle comprehensive session cleanup
     */
    performSessionCleanup() {
        this.clearFormData();
        this.clearImagePreviews();
        
        // Dispatch custom event for other scripts to listen to
        window.dispatchEvent(new CustomEvent('sessionCleanup', {
            detail: { timestamp: Date.now() }
        }));
    }

    /**
     * Logout user
     */
    logout() {
        this.performSessionCleanup();
        window.location.href = '/logout';
    }
}

// Initialize session manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.sessionManager = new SessionManager();
    });
} else {
    window.sessionManager = new SessionManager();
}

/**
 * Session Validator
 * Validates user session status periodically
 */
class SessionValidator {
    constructor() {
        this.CHECK_INTERVAL = 60000; // Check every 60 seconds
        this.checkInterval = null;
        this.init();
    }
    
    /**
     * Initialize validator
     */
    init() {
        // Check on page load
        this.validateSession();
        
        // Setup periodic checks
        this.startPeriodicCheck();
        
        // Listen for logout events
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        // Listen for session cleanup events
        window.addEventListener('sessionCleanup', (e) => {
            console.log('🧹 Session cleanup triggered at', new Date(e.detail.timestamp));
        });
    }
    
    /**
     * Validate current session
     */
    async validateSession() {
        if (!window.sessionManager || !window.sessionManager.isLoggedIn) {
            return;
        }
        
        try {
            const response = await fetch('/check-session');
            
            if (!response.ok) {
                // Session invalid or 401 unauthorized
                if (response.status === 401) {
                    this.handleInvalidSession();
                }
            } else {
                const data = await response.json();
                if (!data.valid) {
                    this.handleInvalidSession();
                }
            }
        } catch (error) {
            console.warn('⚠️ Session validation error (network issue):', error);
            // Don't logout on network errors, just warn
        }
    }
    
    /**
     * Handle invalid session
     */
    handleInvalidSession() {
        if (window.sessionManager) {
            window.sessionManager.performSessionCleanup();
            window.sessionManager.handleSessionTimeout();
        }
    }
    
    /**
     * Start periodic session validation
     */
    startPeriodicCheck() {
        this.checkInterval = setInterval(() => {
            this.validateSession();
        }, this.CHECK_INTERVAL);
    }
    
    /**
     * Cleanup when leaving page
     */
    cleanup() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }
    }
}

// Initialize session validator
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.sessionValidator = new SessionValidator();
    });
} else {
    window.sessionValidator = new SessionValidator();
}
