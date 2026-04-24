/**
 * Chart Initialization Utilities
 * Reusable functions for Chart.js initialization with dynamic data
 */

// ============ LINE CHART ============
function initLineChart(canvasId, label, data, borderColor = '#22a54a', backgroundColor = 'rgba(34, 165, 74, 0.1)') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: label,
                data: data.values || [],
                borderColor: borderColor,
                backgroundColor: backgroundColor,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: borderColor,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    labels: { font: { size: 12, weight: 'bold' } }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { font: { size: 11 } }
                },
                x: {
                    ticks: { font: { size: 11 } }
                }
            }
        }
    });
}

// ============ DOUGHNUT/PIE CHART ============
function initDoughnutChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: data.colors || ['#22a54a', '#1aa179', '#20c997', '#ff9800']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { size: 11, weight: '600' } }
                }
            }
        }
    });
}

// ============ BAR CHART ============
function initBarChart(canvasId, label, data, backgroundColor = '#22a54a', indexAxis = false) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const config = {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: label,
                data: data.values || [],
                backgroundColor: backgroundColor
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                x: { beginAtZero: true },
                y: { beginAtZero: true }
            }
        }
    };
    
    if (indexAxis) {
        config.options.indexAxis = 'y';
    }
    
    return new Chart(ctx.getContext('2d'), config);
}

// ============ UPDATE STAT VALUE ============
function updateStatValue(elementId, value, change = null, isPositive = true) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.textContent = value;
    
    if (change !== null) {
        const changeElement = document.getElementById(elementId.replace('stat-', '') + '-change');
        if (changeElement) {
            changeElement.textContent = change;
            const parentSpan = changeElement.parentElement;
            if (parentSpan) {
                parentSpan.className = isPositive ? 'stat-change positive' : 'stat-change negative';
                parentSpan.innerHTML = `<i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i> ${change} increase from last week`;
            }
        }
    }
}

// ============ FETCH DATA FROM API ============
async function fetchChartData(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error('Failed to fetch data');
        return await response.json();
    } catch (error) {
        console.error('Error fetching chart data:', error);
        return null;
    }
}

// ============ PERIOD SELECTOR ============
function initPeriodSelector(callback) {
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const period = this.getAttribute('data-period');
            if (callback && typeof callback === 'function') {
                callback(period);
            }
        });
    });
}

// ============ SEARCH/FILTER FUNCTIONALITY ============
function initTableSearch(searchInputSelector, tableSelector) {
    const searchInput = document.querySelector(searchInputSelector);
    if (!searchInput) return;
    
    searchInput.addEventListener('keyup', function(e) {
        const query = e.target.value.toLowerCase();
        const rows = document.querySelectorAll(tableSelector + ' tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });
    });
}

// ============ SIDEBAR TOGGLE (Mobile) ============
function initSidebarToggle() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', function(e) {
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        });
    }
}

// ============ INITIALIZE ON DOM READY ============
document.addEventListener('DOMContentLoaded', function() {
    initSidebarToggle();
    initTableSearch('.search-box input', '.table');
});
