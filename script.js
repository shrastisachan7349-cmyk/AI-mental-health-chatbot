const form = document.querySelector("#chatForm");
const input = document.querySelector("#message");
const chat = document.querySelector("#chat");
const sendButton = document.querySelector("#sendButton");
const errorBox = document.querySelector("#error");
const moodSelect = document.querySelector("#mood");
const moodLogButton = document.querySelector("#logMoodButton");
const moodLogStatus = document.querySelector("#moodLogStatus");
const moodChart = document.querySelector("#moodChart");
const moodEmpty = document.querySelector("#moodEmpty");
const moodStorageKey = "mindmate.moodHistory";
const moodScores = { Sad: 1, Stressed: 2, Calm: 3, Happy: 4 };

function readMoodHistory() {
    const saved = localStorage.getItem(moodStorageKey);
    if (!saved) return [];

    const history = JSON.parse(saved);
    if (!Array.isArray(history)) {
        throw new Error("Saved mood history has an unexpected format.");
    }

    return history.filter((entry) =>
        entry
        && Object.prototype.hasOwnProperty.call(moodScores, entry.mood)
        && typeof entry.date === "string"
        && !Number.isNaN(Date.parse(entry.date))
    );
}

function localDateKey(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

function createSvgElement(name, attributes = {}) {
    const element = document.createElementNS("http://www.w3.org/2000/svg", name);
    for (const [attribute, value] of Object.entries(attributes)) {
        element.setAttribute(attribute, value);
    }
    return element;
}

function renderMoodChart(history) {
    moodChart.replaceChildren();

    const today = new Date();
    const days = Array.from({ length: 7 }, (_, index) => {
        const date = new Date(today);
        date.setHours(0, 0, 0, 0);
        date.setDate(date.getDate() - (6 - index));
        return date;
    });
    const dailyScores = new Map();

    for (const entry of history) {
        const date = new Date(entry.date);
        const key = localDateKey(date);
        if (!dailyScores.has(key)) dailyScores.set(key, []);
        dailyScores.get(key).push(moodScores[entry.mood]);
    }

    const plottedDays = days.map((date, index) => {
        const scores = dailyScores.get(localDateKey(date)) || [];
        return {
            date,
            x: 48 + index * 43,
            score: scores.length
                ? scores.reduce((total, score) => total + score, 0) / scores.length
                : null,
        };
    });
    const hasEntries = plottedDays.some((day) => day.score !== null);
    moodEmpty.hidden = hasEntries;
    moodChart.hidden = !hasEntries;
    if (!hasEntries) return;

    for (const [score, label] of [[4, "Happy"], [3, "Calm"], [2, "Stress"], [1, "Sad"]]) {
        const y = 25 + (4 - score) * 28;
        moodChart.append(
            createSvgElement("line", {
                x1: 43,
                y1: y,
                x2: 313,
                y2: y,
                class: "mood-grid-line",
            }),
        );
        const axisLabel = createSvgElement("text", {
            x: 0,
            y: y + 3,
            class: "mood-axis-label",
        });
        axisLabel.textContent = label;
        moodChart.append(axisLabel);
    }

    const points = plottedDays.filter((day) => day.score !== null).map((day) => ({
        ...day,
        y: 25 + (4 - day.score) * 28,
    }));

    if (points.length > 1) {
        moodChart.append(createSvgElement("polyline", {
            points: points.map((point) => `${point.x},${point.y}`).join(" "),
            class: "mood-trend-line",
        }));
    }

    for (const point of points) {
        const pointMood = createSvgElement("circle", {
            cx: point.x,
            cy: point.y,
            r: 5,
            class: "mood-trend-point",
        });
        const pointLabel = createSvgElement("title");
        pointLabel.textContent = `${point.date.toLocaleDateString()}: average mood ${point.score.toFixed(1)} out of 4`;
        pointMood.append(pointLabel);
        moodChart.append(pointMood);
    }

    for (const day of plottedDays) {
        const label = createSvgElement("text", {
            x: day.x,
            y: 151,
            class: "mood-date-label",
            "text-anchor": "middle",
        });
        label.textContent = day.date.toLocaleDateString(undefined, { weekday: "short" });
        moodChart.append(label);
    }
}

function loadMoodHistory() {
    try {
        renderMoodChart(readMoodHistory());
    } catch (error) {
        moodLogStatus.textContent = `Mood history couldn’t be loaded: ${error.message}`;
        moodLogButton.disabled = true;
    }
}

moodLogButton.addEventListener("click", () => {
    try {
        const history = readMoodHistory();
        const now = new Date();
        history.push({ mood: moodSelect.value, date: now.toISOString() });

        const retentionDate = new Date(now);
        retentionDate.setDate(retentionDate.getDate() - 90);
        const recentHistory = history.filter((entry) => new Date(entry.date) >= retentionDate);
        localStorage.setItem(moodStorageKey, JSON.stringify(recentHistory));
        renderMoodChart(recentHistory);
        moodLogStatus.textContent = `Logged ${moodSelect.value.toLowerCase()} for today.`;
    } catch (error) {
        moodLogStatus.textContent = `Mood couldn’t be saved: ${error.message}`;
    }
});

loadMoodHistory();

function addMessage(text, sender, crisis = false) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${sender}${crisis ? " crisis" : ""}`;

    const bubble = document.createElement("p");
    bubble.textContent = text;

    const time = document.createElement("time");
    time.textContent = "Just now";

    wrapper.append(bubble, time);
    chat.appendChild(wrapper);
    chat.scrollTop = chat.scrollHeight;
}

async function sendMessage(text) {
    const message = text.trim();
    if (!message) return;

    errorBox.textContent = "";
    addMessage(message, "user");
    input.value = "";
    sendButton.disabled = true;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                mood: document.querySelector("#mood").value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to send the message.");
        }

        addMessage(data.reply, "bot", data.crisis);
    } catch (error) {
        errorBox.textContent = `${error.message} Please try again.`;
    } finally {
        sendButton.disabled = false;
        input.focus();
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(input.value);
});

document.querySelector("#suggestions").addEventListener("click", (event) => {
    if (event.target.matches("button")) {
        sendMessage(event.target.textContent);
    }
});

document.querySelector("#clearButton").addEventListener("click", () => {
    chat.replaceChildren();
    addMessage("Hello! I’m glad you’re here. How are you feeling today?", "bot");
    errorBox.textContent = "";
});

let breathingTimer;

document.querySelector("#breathingButton").addEventListener("click", () => {
    const status = document.querySelector("#breathingStatus");
    let step = 0;

    clearInterval(breathingTimer);
    status.textContent = "Breathe in gently…";

    breathingTimer = setInterval(() => {
        step += 1;

        if (step >= 6) {
            clearInterval(breathingTimer);
            status.textContent = "Pause here and notice how you feel.";
            return;
        }

        status.textContent = step % 2
            ? "Breathe out slowly…"
            : "Breathe in gently…";
    }, 4000);
});