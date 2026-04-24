// Dashboard shared utilities and chart initialization

/**
 * Initialize Sales Chart
 */
function initializeSalesChart() {
    const salesCanvas = document.getElementById('salesChart');
    if (!salesCanvas) return;
    
    const salesCtx = salesCanvas.getContext('2d');
    new Chart(salesCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [
                {
                    label: 'Sales',
                    data: [3200, 4100, 3800, 5200, 4900, 6100, 5800],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#28a745',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#2c3e50',
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                }
            }
        }
    });
}

/**
 * Initialize Category Distribution Chart
 */
function initializeCategoryChart() {
    const categoryCanvas = document.getElementById('categoryChart');
    if (!categoryCanvas) return;
    
    const categoryCtx = categoryCanvas.getContext('2d');
    new Chart(categoryCtx, {
        type: 'doughnut',
        data: {
            labels: ['Indoor Plants', 'Outdoor Plants', 'Accessories', 'Pots'],
            datasets: [
                {
                    data: [35, 25, 20, 20],
                    backgroundColor: [
                        '#28a745',
                        '#20c997',
                        '#17a2b8',
                        '#ffc107'
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#2c3e50',
                        font: {
                            size: 12,
                            weight: '600'
                        },
                        padding: 15
                    }
                }
            }
        }
    });
}

/**
 * Search functionality for tables
 */
function setupTableSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    searchInput.addEventListener('keyup', function(e) {
        const query = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('table tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });
    });
}

/**
 * Toggle sidebar on mobile
 */
function setupSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    
    const isMobile = window.innerWidth <= 576;
    if (isMobile) {
        sidebar.classList.remove('active');
    }
}

/**
 * Navigate to different admin pages
 */
function navigateTo(page) {
    // Get current base URL and replace the last segment with the page name
    const currentUrl = window.location.pathname;
    const basePath = currentUrl.substring(0, currentUrl.lastIndexOf('/'));
    window.location.href = `${basePath}/${page}`;
}

/**
 * Update notification badge dynamically
 */
function updateNotificationCount(count) {
    const badge = document.getElementById('notificationCount');
    if (badge) {
        badge.textContent = count;
    }
}

/**
 * Initialize all dashboard features
 */
document.addEventListener('DOMContentLoaded', function() {
    setupTableSearch();
    setupSidebarToggle();
});
