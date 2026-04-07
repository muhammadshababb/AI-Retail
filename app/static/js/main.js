// document ready
document.addEventListener("DOMContentLoaded", () => {

    // Dismiss flashes automatically after 4 seconds
    setTimeout(() => {
        const flashes = document.querySelectorAll('.flash');
        flashes.forEach(f => {
            f.style.opacity = '0';
            f.style.transform = 'translateY(20px)';
            f.style.transition = 'all 0.4s ease';
            setTimeout(() => f.remove(), 400);
        });
    }, 4000);
    
    // Allow manual dismiss
    document.querySelectorAll('.flash').forEach(f => {
        f.addEventListener('click', () => {
            f.style.opacity = '0';
            setTimeout(() => f.remove(), 400);
        });
    });
    
    // Theme toggling
    const themeBtn = document.getElementById('themeToggle');
    if(themeBtn) {
        themeBtn.addEventListener('click', () => {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const target = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', target);
            themeBtn.innerHTML = target === 'dark' ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
            if(window.myCharts) { // redraw charts on theme switch for text colors
                Object.values(window.myCharts).forEach(c => {
                    c.options.scales.x.ticks.color = target === 'dark' ? '#94A3B8' : '#64748B';
                    c.options.scales.y.ticks.color = target === 'dark' ? '#94A3B8' : '#64748B';
                    c.update();
                });
            }
        });
    }

    // Dashboard loading logic
    if (window.CURRENT_DATASET_ID) {
        loadDashboardData([]);
        loadInsights();
    }
});

window.myCharts = {};
let currentFilters = {};

function applyFilter(column, value) {
    if (value === "") {
        delete currentFilters[column];
    } else {
        currentFilters[column] = value;
    }
    
    const filtersArray = Object.keys(currentFilters).map(k => ({col: k, val: currentFilters[k]}));
    loadDashboardData(filtersArray);
}

async function loadDashboardData(filters = []) {
    try {
        const id = window.CURRENT_DATASET_ID;
        const res = await fetch(`/api/data/${id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filters})
        });
        const data = await res.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }

        renderKPIs(data.kpis);
        if(filters.length === 0) renderFilters(data.filters); // only re-render filters on first load or clear
        
        // Also fetch forecast with same filters
        loadForecast(filters);

        renderCategoryCharts(data.charts);
        
    } catch (e) {
        console.error("Error loading dashboard data:", e);
    }
}

async function loadForecast(filters = []) {
    try {
        const id = window.CURRENT_DATASET_ID;
        const res = await fetch(`/api/forecast/${id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filters, days: 30})
        });
        const data = await res.json();
        
        const badge = document.getElementById('forecastBadge');
        if (badge) {
            if (data.warning) {
                badge.innerText = "HISTORICAL ONLY";
                badge.style.color = "var(--warning)";
                badge.style.background = "rgba(245, 158, 11, 0.1)";
                badge.style.borderColor = "rgba(245, 158, 11, 0.2)";
            } else {
                badge.innerText = "NEXT 30 DAYS";
                badge.style.color = "var(--success)";
                badge.style.background = "rgba(16,185,129,0.1)";
                badge.style.borderColor = "rgba(16,185,129,0.2)";
            }
        }

        if(data.error) {
            console.warn("Forecast error:", data.error);
            if (data.historical && Object.keys(data.historical).length > 0) {
                renderTrendChart(data);
            }
            return;
        }
        
        renderTrendChart(data);
    } catch (e) {
        console.error("Forecast error:", e);
    }
}

async function loadInsights() {
    try {
        const id = window.CURRENT_DATASET_ID;
        const res = await fetch(`/api/insights/${id}`);
        const data = await res.json();
        
        const container = document.getElementById('insightsContainer');
        container.innerHTML = '';
        
        data.insights.forEach(ins => {
            container.innerHTML += `
                <div class="insight-card ${ins.type}">
                    <h4><i class="fa-solid fa-circle-info" style="margin-right: 8px;"></i>${ins.title}</h4>
                    <p>${ins.message}</p>
                </div>
            `;
        });
    } catch (e) {
        console.error("Insights error:", e);
    }
}

function renderKPIs(kpis) {
    const grid = document.getElementById('kpiGrid');
    grid.innerHTML = '';
    Object.keys(kpis).forEach(k => {
        let val = kpis[k];
        if (typeof val === 'number') {
            if (val > 1000) val = val.toLocaleString();
        }
        grid.innerHTML += `
            <div class="kpi-card">
                <span class="kpi-title">${k}</span>
                <span class="kpi-value">${val}</span>
            </div>
        `;
    });
}

function renderFilters(filters) {
    const cont = document.getElementById('filtersContainer');
    cont.style.display = 'flex';
    let html = '';
    
    Object.keys(filters).forEach(k => {
        html += `
            <select class="filter-select" onchange="applyFilter('${k}', this.value)">
                <option value="">All ${k}</option>
        `;
        filters[k].forEach(opt => {
            const selected = currentFilters[k] === opt ? 'selected' : '';
            html += `<option value="${opt}" ${selected}>${opt}</option>`;
        });
        html += `</select>`;
    });
    
    // Add clear filter button with a modern look
    if (Object.keys(currentFilters).length > 0) {
        html += `<button onclick="currentFilters={}; loadDashboardData();" style="
            background: rgba(239, 68, 68, 0.1); 
            color: var(--danger); 
            border: 1px solid rgba(239, 68, 68, 0.3); 
            padding: 10px 16px; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 14px; 
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;">
            <i class="fa-solid fa-xmark"></i> Reset Filters
        </button>`;
    }
    
    cont.innerHTML = html;
}

function getChartColors() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    return {
        text: isDark ? '#94A3B8' : '#64748B',
        grid: isDark ? '#1E293B' : '#E2E8F0',
        primary: '#3B82F6',
        forecast: '#10B981'
    };
}

function renderTrendChart(forecastData) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    const colors = getChartColors();
    
    if(window.myCharts['trend']) window.myCharts['trend'].destroy();
    
    const histKeys = Object.keys(forecastData.historical);
    const fcstKeys = Object.keys(forecastData.forecast);
    
    const allLabels = [...histKeys, ...fcstKeys];
    
    const histValues = histKeys.map(k => forecastData.historical[k]);
    // padding for forecasting line so they connect
    const fcstValues = Array(histKeys.length - 1).fill(null);
    fcstValues.push(histValues[histValues.length-1]);
    fcstKeys.forEach(k => fcstValues.push(forecastData.forecast[k]));

    window.myCharts['trend'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: 'Historical',
                    data: [...histValues, ...Array(fcstKeys.length).fill(null)],
                    borderColor: colors.primary,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'AI Forecast',
                    data: fcstValues,
                    borderColor: colors.forecast,
                    borderDash: [5, 5],
                    tension: 0.4,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: colors.text }, grid: { color: colors.grid } },
                y: { ticks: { color: colors.text }, grid: { color: colors.grid } }
            },
            plugins: {
                legend: { labels: { color: colors.text } }
            }
        }
    });

}

function renderCategoryCharts(chartsData) {
    const container = document.getElementById('categoryChartsContainer');
    container.innerHTML = '<div class="panel-header"><span class="panel-title">Top Categories</span></div>';
    
    const colors = getChartColors();

    Object.keys(chartsData).forEach((chartName, i) => {
        if(chartName === "Weekly Trend") return; // skipped
        
        container.innerHTML += `<div style="margin-bottom: 24px;">
            <h5 style="margin-bottom: 12px; color: var(--text-muted);">${chartName}</h5>
            <canvas id="catChart_${i}" height="180"></canvas>
        </div>`;
    });

    Object.keys(chartsData).forEach((chartName, i) => {
        if(chartName === "Weekly Trend") return;
        const data = chartsData[chartName];
        const ctx = document.getElementById(`catChart_${i}`).getContext('2d');
        
        let cId = `catChart_${i}`;
        if(window.myCharts[cId]) window.myCharts[cId].destroy();

        window.myCharts[cId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    label: chartName,
                    data: Object.values(data),
                    backgroundColor: colors.primary,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                indexAxis: 'y', // horizontal bar
                scales: {
                    x: { ticks: { color: colors.text }, grid: { color: colors.grid } },
                    y: { ticks: { color: colors.text }, grid: { display: false } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    });
}
