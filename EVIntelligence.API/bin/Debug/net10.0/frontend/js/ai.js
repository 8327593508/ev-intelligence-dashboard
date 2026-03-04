const chatContainer = document.getElementById("chatContainer");
const inputBox = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

function addMessage(text, sender, chartData = null) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);

    if (sender === "bot") {
        msgDiv.innerHTML = `
            <div class="bot-header">🤖 Moxie</div>
            <div>${text}</div>
        `;
    } else {
        msgDiv.textContent = text;
    }

    chatContainer.appendChild(msgDiv);

    // Render chart if available
    if (chartData && chartData.labels && chartData.values) {
        renderChart(chartData, msgDiv);
    }

    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showTyping() {
    const typingDiv = document.createElement("div");
    typingDiv.classList.add("message", "bot", "typing");
    typingDiv.id = "typingIndicator";
    typingDiv.innerHTML = `<div class="bot-header">🤖 Moxie</div>Analyzing EV data...`;
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTyping() {
    const typing = document.getElementById("typingIndicator");
    if (typing) typing.remove();
}

function renderChart(chartData, parentDiv) {
    const chartBox = document.createElement("div");
    chartBox.classList.add("chart-box");

    const canvas = document.createElement("canvas");
    chartBox.appendChild(canvas);
    parentDiv.appendChild(chartBox);

    const type = chartData.type || "bar";

    new Chart(canvas, {
        type: type,
        data: {
            labels: chartData.labels,
            datasets: [{
                label: "EV Analytics",
                data: chartData.values
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: "#fff" }
                }
            },
            scales: {
                x: { ticks: { color: "#fff" } },
                y: { ticks: { color: "#fff" } }
            }
        }
    });
}

async function sendMessage() {
    const question = inputBox.value.trim();
    if (!question) return;

    addMessage(question, "user");
    inputBox.value = "";
    showTyping();

    try {
        const response = await fetch("/api/ai/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question: question })
        });

        const data = await response.json();
        removeTyping();

        if (data.answer) {
            addMessage(data.answer, "bot", data.chart || null);
        } else {
            addMessage("I couldn't process that EV query. Please try again.", "bot");
        }
    } catch (error) {
        removeTyping();
        addMessage("⚠️ Unable to connect to Moxie AI service.", "bot");
    }
}

// EVENTS
sendBtn.addEventListener("click", sendMessage);
inputBox.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});