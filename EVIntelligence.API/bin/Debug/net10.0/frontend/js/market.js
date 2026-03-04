// GLOBAL CHART STYLE (same theme as your dashboard)
Chart.defaults.color = "#cbd5f5";
Chart.defaults.borderColor = "#1e293b";

// Safe fetch helper (shows real errors in console)
async function fetchData(url) {
    try {
        const res = await fetch(url);
        if (!res.ok) {
            console.error("API FAILED:", url, res.status);
            return null;
        }
        return await res.json();
    } catch (err) {
        console.error("FETCH ERROR:", err);
        return null;
    }
}

/* =========================================================
   1️⃣ MANUFACTURER SALES (Clustered Bar)
   Uses: /api/dashboard/manufacturer-sales  ✔ EXISTS
========================================================= */
async function loadManufacturerSales() {
    const data = await fetchData("/api/dashboard/manufacturer-sales");
    if (!data) return;

    const canvas = document.getElementById("manufacturerChart");
    if (!canvas) return;

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.labels,
            datasets: [{
                label: "Total Sales",
                data: data.values,
                backgroundColor: "#38bdf8",
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } }
        }
    });
}

/* =========================================================
   2️⃣ MARKET GROWTH AREA
   Uses: ev_india_monthly via /api/dashboard/ev-trend ✔ EXISTS
========================================================= */
async function loadMarketGrowth() {
    const data = await fetchData("/api/dashboard/ev-trend");
    if (!data) return;

    const canvas = document.getElementById("marketGrowthChart");
    if (!canvas) return;

    new Chart(canvas, {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [{
                label: "EV Market Growth",
                data: data.historical,
                borderColor: "#22c55e",
                backgroundColor: "rgba(34,197,94,0.25)",
                fill: true,
                tension: 0.4,
                pointRadius: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } }
        }
    });
}

/* =========================================================
   3️⃣ MANUFACTURER TREND LINE
   (Reusing manufacturer-sales endpoint correctly)
========================================================= */
async function loadManufacturerTrend() {
    const data = await fetchData("/api/dashboard/manufacturer-sales");
    if (!data) return;

    const canvas = document.getElementById("trendChartMarket");
    if (!canvas) return;

    new Chart(canvas, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: [{
                label: "Manufacturer Sales Trend",
                data: data.values,
                borderColor: "#22d3ee",
                backgroundColor: "rgba(34,211,238,0.15)",
                fill: true,
                tension: 0.4,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } }
        }
    });
}

/* =========================================================
   4️⃣ VEHICLE TYPE DISTRIBUTION
   Uses your real DB tables: ev_registrations + vehicle_types
   (Requires endpoint I will give below)
========================================================= */
async function loadVehicleTypes() {
    const data = await fetchData("/api/dashboard/vehicle-types");
    if (!data) return;

    const canvas = document.getElementById("vehicleTypeChart");
    if (!canvas) return;

    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    "#38bdf8",
                    "#a78bfa",
                    "#f472b6",
                    "#22c55e",
                    "#facc15"
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } }
        }
    });
}

/* =========================================================
   5️⃣ PRICE VS RANGE (SCATTER)
   Uses: /api/dashboard/scatter ✔ EXISTS
========================================================= */
async function loadPriceRange() {
    const data = await fetchData("/api/dashboard/scatter");
    if (!data || !data.points) return;

    const canvas = document.getElementById("priceRangeChart");
    if (!canvas) return;

    new Chart(canvas, {
        type: "scatter",
        data: {
            datasets: [{
                label: "Price vs Range",
                data: data.points,
                backgroundColor: "#f472b6",
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: "Price" } },
                y: { title: { display: true, text: "Range (KM)" } }
            }
        }
    });
}

/* =========================================================
   6️⃣ BATTERY VS RANGE RADAR
   Uses ev_vehicle_specs via scatter endpoint
========================================================= */
async function loadBatteryRadar() {
    const data = await fetchData("/api/dashboard/scatter");
    if (!data || !data.points || data.points.length === 0) return;

    const sample = data.points.slice(0, 6);
    const labels = sample.map((_, i) => `EV ${i + 1}`);
    const range = sample.map(p => p.y);
    const priceScaled = sample.map(p => p.x / 100000);

    const canvas = document.getElementById("radarChart");
    if (!canvas) return;

    new Chart(canvas, {
        type: "radar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Range (KM)",
                    data: range,
                    borderColor: "#22c55e",
                    backgroundColor: "rgba(34,197,94,0.25)"
                },
                {
                    label: "Price (Scaled)",
                    data: priceScaled,
                    borderColor: "#facc15",
                    backgroundColor: "rgba(250,204,21,0.25)"
                }
            ]
        },
        options: {
            responsive: true
        }
    });
}

// LOAD ALL ANALYTICS CHARTS (FINAL)
document.addEventListener("DOMContentLoaded", () => {
    loadManufacturerSales();
    loadMarketGrowth();
    loadManufacturerTrend();
    loadVehicleTypes();
    loadPriceRange();
    loadBatteryRadar();
});