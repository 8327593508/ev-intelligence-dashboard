const API = "http://localhost:5212/api/dashboard";

async function fetchData(endpoint) {
    try {
        const res = await fetch(`${API}/${endpoint}`);
        if (!res.ok) {
            console.error("API Error:", endpoint);
            return null;
        }
        return await res.json();
    } catch (err) {
        console.error("Fetch Failed:", err);
        return null;
    }
}

// ================= 1️⃣ Chargers by State (Column) =================
async function loadStateChargers() {
    const data = await fetchData("chargers-by-state"); // ✅ CORRECT ENDPOINT
    if (!data) return;

    new Chart(document.getElementById("chargerStateChart"), {
        type: "bar",
        data: {
            labels: data.states,
            datasets: [{
                label: "Total Chargers",
                data: data.values,
                backgroundColor: "#22d3ee",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: "#e2e8f0" } }
            },
            scales: {
                x: { ticks: { color: "#e2e8f0" } },
                y: { ticks: { color: "#e2e8f0" } }
            }
        }
    });
}

// ================= 2️⃣ Price vs Range (Scatter) =================
async function loadPriceRangeInfra() {
    const data = await fetchData("infra-price-range"); // ✅ NEW ENDPOINT
    if (!data) return;

    new Chart(document.getElementById("priceRangeInfra"), {
        type: "scatter",
        data: {
            datasets: [{
                label: "Price vs Range",
                data: data.points,
                backgroundColor: "#f97316",
                pointRadius: 6
            }]
        },
        options: {
            scales: {
                x: {
                    title: { display: true, text: "Price" },
                    ticks: { color: "#e2e8f0" }
                },
                y: {
                    title: { display: true, text: "Range (KM)" },
                    ticks: { color: "#e2e8f0" }
                }
            },
            plugins: {
                legend: { labels: { color: "#e2e8f0" } }
            }
        }
    });
}

// ================= 3️⃣ Battery vs Range Radar =================
async function loadBatteryRadar() {
    const data = await fetchData("infra-battery-radar"); // ✅ NEW
    if (!data) return;

    new Chart(document.getElementById("batteryRadar"), {
        type: "radar",
        data: {
            labels: data.labels,
            datasets: [{
                label: "Range (Top EV Models)",
                data: data.values,
                backgroundColor: "rgba(34,211,238,0.3)",
                borderColor: "#22d3ee",
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: "#e2e8f0" } }
            },
            scales: {
                r: {
                    ticks: { color: "#e2e8f0" },
                    grid: { color: "#1e293b" }
                }
            }
        }
    });
}

// ================= 4️⃣ Infrastructure Growth Area =================
async function loadInfraGrowth() {
    const data = await fetchData("monthly"); // ✅ already exists
    if (!data) return;

    new Chart(document.getElementById("infraGrowth"), {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [{
                label: "EV Infrastructure Growth Trend",
                data: data.values,
                borderColor: "#4ade80",
                backgroundColor: "rgba(74,222,128,0.2)",
                fill: true,
                tension: 0.4,
                pointRadius: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: "#e2e8f0" } }
            },
            scales: {
                x: { ticks: { color: "#e2e8f0" } },
                y: { ticks: { color: "#e2e8f0" } }
            }
        }
    });
}

// ================= 5️⃣ Power vs Connectors (Bubble) =================
async function loadBubbleChart() {
    const data = await fetchData("power-connectors"); // ✅ already exists
    if (!data) return;

    new Chart(document.getElementById("bubbleChart"), {
        type: "bubble",
        data: {
            datasets: [{
                label: "Power vs Connectors",
                data: data.points,
                backgroundColor: "#a78bfa"
            }]
        },
        options: {
            plugins: {
                legend: { labels: { color: "#e2e8f0" } }
            },
            scales: {
                x: {
                    title: { display: true, text: "Power (kW)" },
                    ticks: { color: "#e2e8f0" }
                },
                y: {
                    title: { display: true, text: "Connectors" },
                    ticks: { color: "#e2e8f0" }
                }
            }
        }
    });
}

// ================= 6️⃣ Charger Level Distribution =================
async function loadChargerLevel() {
    const data = await fetchData("infra-charger-level"); // ✅ NEW
    if (!data) return;

    new Chart(document.getElementById("chargerLevelChart"), {
        type: "doughnut",
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    "#22d3ee",
                    "#4ade80",
                    "#f97316",
                    "#a78bfa",
                    "#facc15"
                ]
            }]
        },
        options: {
            plugins: {
                legend: { labels: { color: "#e2e8f0" } }
            }
        }
    });
}

// ================= INIT =================
document.addEventListener("DOMContentLoaded", async () => {
    await loadStateChargers();
    await loadPriceRangeInfra();
    await loadBatteryRadar();
    await loadInfraGrowth();
    await loadBubbleChart();
    await loadChargerLevel();
});