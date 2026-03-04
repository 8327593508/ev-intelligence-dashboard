const API = "http://localhost:5212/api/dashboard";

async function fetchJSON(endpoint) {
    const res = await fetch(`${API}/${endpoint}`);
    return await res.json();
}

async function loadKPIs() {
    const data = await fetchJSON("kpis");
    document.getElementById("total-ev").innerText = Number(data.totalEV || 0).toLocaleString();
    document.getElementById("chargers").innerText = Number(data.totalChargers || 0).toLocaleString();
    document.getElementById("forecast").innerText = Number(data.nextForecast || 0).toLocaleString();
    document.getElementById("states").innerText = data.activeStates || 0;
}

// 📈 EV Growth (Historical + Forecast) — EXACT like your screenshot
async function loadTrendChart() {
    const data = await fetchJSON("ev-trend");

    new Chart(document.getElementById("trendChart"), {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: "Historical EV",
                    data: data.historical,
                    borderColor: "#22d3ee",
                    borderWidth: 2,
                    pointRadius: 0, // removes bubbles (you asked)
                    tension: 0.3,
                    fill: false
                },
                {
                    label: "Forecast (LSTM)",
                    data: data.forecast,
                    borderColor: "#facc15",
                    borderDash: [6, 6], // thin dotted future line
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            plugins: { legend: { labels: { color: "#e2e8f0" } } },
            scales: {
                x: { ticks: { color: "#94a3b8" } },
                y: { ticks: { color: "#94a3b8" } }
            }
        }
    });
}

// 📊 Monthly EV Registrations (BAR – same as screenshot)
async function loadMonthlyChart() {
    const data = await fetchJSON("monthly");

    new Chart(document.getElementById("monthlyChart"), {
        type: "bar",
        data: {
            labels: data.dates,
            datasets: [{
                label: "Monthly EV",
                data: data.values,
                backgroundColor: "#06b6d4"
            }]
        },
        options: {
            plugins: { legend: { labels: { color: "#e2e8f0" } } }
        }
    });
}

// 🗺 State-wise EV Adoption (Horizontal Bar)
async function loadStateChart() {
    const data = await fetchJSON("state-adoption");

    new Chart(document.getElementById("stateChart"), {
        type: "bar",
        data: {
            labels: data.states,
            datasets: [{
                label: "Total EV",
                data: data.values,
                backgroundColor: "#a78bfa"
            }]
        },
        options: {
            indexAxis: "y",
            plugins: { legend: { labels: { color: "#e2e8f0" } } }
        }
    });
}

// ⚡ EV vs Chargers (Clustered Columns)
async function loadInfraGapChart() {
    const data = await fetchJSON("ev-vs-chargers");

    new Chart(document.getElementById("infraGapChart"), {
        type: "bar",
        data: {
            labels: data.states,
            datasets: [
                {
                    label: "EV",
                    data: data.ev,
                    backgroundColor: "#22d3ee"
                },
                {
                    label: "Chargers",
                    data: data.chargers,
                    backgroundColor: "#fb923c"
                }
            ]
        }
    });
}

// 📉 Histogram (FIXED – using monthly EV distribution)
async function loadHistogram() {
    const data = await fetchJSON("monthly");

    new Chart(document.getElementById("histChart"), {
        type: "bar",
        data: {
            labels: data.values.map(v => Math.round(v)),
            datasets: [{
                label: "EV Distribution",
                data: data.values,
                backgroundColor: "#10b981"
            }]
        },
        options: {
            plugins: { legend: { labels: { color: "#e2e8f0" } } }
        }
    });
}

// 🔬 Scatter (EV vs Infrastructure)
async function loadScatter() {
    const data = await fetchJSON("scatter");

    new Chart(document.getElementById("scatterChart"), {
        type: "scatter",
        data: {
            datasets: [{
                label: "Price vs Range",
                data: data.points,
                backgroundColor: "#f43f5e"
            }]
        }
    });
}

async function init() {
    await loadKPIs();
    await loadTrendChart();
    await loadMonthlyChart();
    await loadStateChart();
    await loadInfraGapChart();
    await loadHistogram();
    await loadScatter();
}

init();