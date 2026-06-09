const jsonHeaders = { "Content-Type": "application/json" };

function showToast(message) {
    const toast = document.querySelector("#toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("visible");
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 2600);
}

async function apiFetch(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        let message = `Request failed (${response.status})`;
        try {
            const data = await response.json();
            message = data.detail || JSON.stringify(data);
        } catch (error) {
            message = response.statusText || message;
        }
        throw new Error(message);
    }
    if (response.status === 204) return null;
    return response.json();
}

function formatTime(value) {
    if (!value) return "";
    return new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    }).format(new Date(value));
}

function updateTotals(payload) {
    const totalIn = document.querySelector("#total-in");
    const totalOut = document.querySelector("#total-out");
    const totalAll = document.querySelector("#total-all");
    if (totalIn) totalIn.textContent = payload.total_in ?? 0;
    if (totalOut) totalOut.textContent = payload.total_out ?? 0;
    if (totalAll) totalAll.textContent = payload.total ?? 0;
}

function updateCamera(payload) {
    const camera = document.querySelector("#camera-status");
    if (!camera || !payload.camera) return;
    const fps = Number(payload.camera.fps || 0).toFixed(1);
    camera.textContent = `camera: ${payload.camera.status} | ${fps} fps`;
}

function updateRecentEvents(events) {
    const body = document.querySelector("#recent-events");
    if (!body) return;
    body.innerHTML = "";
    if (!events || events.length === 0) {
        body.innerHTML = '<tr><td colspan="4">No events yet</td></tr>';
        return;
    }
    for (const event of events) {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${formatTime(event.occurred_at)}</td>
            <td>${event.counting_line_name || "Unassigned"}</td>
            <td>${event.direction}</td>
            <td>${event.track_id || ""}</td>
        `;
        body.appendChild(row);
    }
}

function updateLineSummary(lines) {
    const list = document.querySelector("#line-summary");
    if (!list) return;
    list.innerHTML = "";
    if (!lines || lines.length === 0) {
        list.innerHTML = '<p class="line-item">No counts recorded today</p>';
        return;
    }
    for (const line of lines) {
        const item = document.createElement("div");
        item.className = "line-item";
        item.innerHTML = `
            <strong>${line.counting_line_name || "Unassigned"}</strong>
            <span>in ${line.in_count} | out ${line.out_count} | total ${line.total}</span>
        `;
        list.appendChild(item);
    }
}

async function pollLive() {
    const stats = await apiFetch("/api/stats/daily/");
    const events = await apiFetch("/api/events/");
    updateTotals(stats);
    updateLineSummary(stats.lines || []);
    updateRecentEvents(events.slice(0, 10));
}

function connectLiveUpdates() {
    if (!document.querySelector("#total-in")) return;

    if ("EventSource" in window) {
        const source = new EventSource("/stream/live/");
        source.addEventListener("update", (event) => {
            const payload = JSON.parse(event.data);
            updateTotals(payload);
            updateCamera(payload);
            updateLineSummary(payload.counters || []);
            updateRecentEvents(payload.recent_events || []);
        });
        source.onerror = () => {
            source.close();
            pollLive().catch((error) => showToast(error.message));
            window.setInterval(() => pollLive().catch(() => {}), 5000);
        };
    } else {
        pollLive().catch((error) => showToast(error.message));
        window.setInterval(() => pollLive().catch(() => {}), 5000);
    }
}

function linePayload() {
    return {
        name: document.querySelector("#line-name").value,
        start_x: Number(document.querySelector("#start-x").value),
        start_y: Number(document.querySelector("#start-y").value),
        end_x: Number(document.querySelector("#end-x").value),
        end_y: Number(document.querySelector("#end-y").value),
        is_active: document.querySelector("#line-active").checked,
    };
}

function resetLineForm() {
    const form = document.querySelector("#line-form");
    if (!form) return;
    form.reset();
    document.querySelector("#line-id").value = "";
    document.querySelector("#line-active").checked = true;
}

function editLine(line) {
    document.querySelector("#line-id").value = line.id;
    document.querySelector("#line-name").value = line.name;
    document.querySelector("#start-x").value = line.start_x;
    document.querySelector("#start-y").value = line.start_y;
    document.querySelector("#end-x").value = line.end_x;
    document.querySelector("#end-y").value = line.end_y;
    document.querySelector("#line-active").checked = line.is_active;
}

async function loadLines() {
    const table = document.querySelector("#line-table");
    if (!table) return;
    const lines = await apiFetch("/api/counting-lines/");
    table.innerHTML = "";
    for (const line of lines) {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${line.name}</td>
            <td>${line.start_x},${line.start_y} -> ${line.end_x},${line.end_y}</td>
            <td>${line.is_active ? "active" : "inactive"}</td>
            <td class="button-row">
                <button class="button small ghost" type="button" data-edit="${line.id}">Edit</button>
                <button class="button small danger" type="button" data-delete="${line.id}">Delete</button>
            </td>
        `;
        row.querySelector("[data-edit]").addEventListener("click", () => editLine(line));
        row.querySelector("[data-delete]").addEventListener("click", async () => {
            try {
                await apiFetch(`/api/counting-lines/${line.id}/`, { method: "DELETE" });
                await loadLines();
                showToast("Counting line deleted");
            } catch (error) {
                showToast(error.message);
            }
        });
        table.appendChild(row);
    }
}

async function loadNetwork() {
    const form = document.querySelector("#network-form");
    if (!form) return;
    const data = await apiFetch("/api/network-config/");
    document.querySelector("#hostname").value = data.hostname || "";
    document.querySelector("#interface").value = data.interface || "";
    document.querySelector("#dhcp-enabled").checked = Boolean(data.dhcp_enabled);
    document.querySelector("#ip-address").value = data.ip_address || "";
    document.querySelector("#netmask").value = data.netmask || "";
    document.querySelector("#gateway").value = data.gateway || "";
}

function bindSettings() {
    const lineForm = document.querySelector("#line-form");
    if (!lineForm) return;

    lineForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const id = document.querySelector("#line-id").value;
        const url = id ? `/api/counting-lines/${id}/` : "/api/counting-lines/";
        const method = id ? "PATCH" : "POST";
        try {
            await apiFetch(url, { method, headers: jsonHeaders, body: JSON.stringify(linePayload()) });
            resetLineForm();
            await loadLines();
            showToast("Counting line saved");
        } catch (error) {
            showToast(error.message);
        }
    });

    document.querySelector("#line-reset").addEventListener("click", resetLineForm);

    const networkForm = document.querySelector("#network-form");
    networkForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = {
            hostname: document.querySelector("#hostname").value,
            interface: document.querySelector("#interface").value,
            dhcp_enabled: document.querySelector("#dhcp-enabled").checked,
            ip_address: document.querySelector("#ip-address").value,
            netmask: document.querySelector("#netmask").value,
            gateway: document.querySelector("#gateway").value,
        };
        try {
            await apiFetch("/api/network-config/", { method: "PATCH", headers: jsonHeaders, body: JSON.stringify(payload) });
            showToast("Network settings saved");
        } catch (error) {
            showToast(error.message);
        }
    });

    loadLines().catch((error) => showToast(error.message));
    loadNetwork().catch((error) => showToast(error.message));
}

function bindRecording() {
    const start = document.querySelector("#record-start");
    const stop = document.querySelector("#record-stop");
    if (!start || !stop) return;

    start.addEventListener("click", async () => {
        try {
            await apiFetch("/api/recording/", { method: "POST", headers: jsonHeaders, body: JSON.stringify({ action: "start" }) });
            showToast("Recording started");
        } catch (error) {
            showToast(error.message);
        }
    });

    stop.addEventListener("click", async () => {
        try {
            await apiFetch("/api/recording/", { method: "POST", headers: jsonHeaders, body: JSON.stringify({ action: "stop" }) });
            showToast("Recording stopped");
        } catch (error) {
            showToast(error.message);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    connectLiveUpdates();
    bindSettings();
    bindRecording();
});
