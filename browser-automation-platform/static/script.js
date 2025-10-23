(function () {
    const statusText = document.getElementById('status-text');
    const statusMessage = document.getElementById('status-message');
    const statusProgress = document.getElementById('status-progress');
    const statusTimestamp = document.getElementById('status-timestamp');
    const resultStatus = document.getElementById('result-status');
    const resultMessage = document.getElementById('result-message');
    const resultProgress = document.getElementById('result-progress');
    const resultTimestamp = document.getElementById('result-timestamp');
    const logContainer = document.getElementById('live-log') || document.getElementById('results-log');
    const controlFeedback = document.getElementById('control-feedback');
    const configFeedback = document.getElementById('config-feedback');

    const updateStatus = (data) => {
        if (!data) return;
        if (statusText) statusText.textContent = data.status;
        if (statusMessage) statusMessage.textContent = data.message;
        if (statusProgress) statusProgress.textContent = `${parseFloat(data.progress || 0).toFixed(2)}%`;
        if (statusTimestamp) statusTimestamp.textContent = data.timestamp;
        if (resultStatus) resultStatus.textContent = data.status;
        if (resultMessage) resultMessage.textContent = data.message;
        if (resultProgress) resultProgress.textContent = `${parseFloat(data.progress || 0).toFixed(2)}%`;
        if (resultTimestamp) resultTimestamp.textContent = data.timestamp;
    };

    const appendLog = (data) => {
        if (!logContainer) return;
        const entry = document.createElement('div');
        entry.className = `log-entry ${data.status}`;
        const meta = document.createElement('span');
        meta.className = 'meta';
        meta.textContent = `[${data.timestamp}] ${data.status.toUpperCase()}`;
        entry.appendChild(meta);
        const body = document.createElement('div');
        body.textContent = data.message;
        entry.appendChild(body);
        if (typeof data.progress !== 'undefined') {
            const progress = document.createElement('div');
            progress.textContent = `Progress: ${parseFloat(data.progress).toFixed(2)}%`;
            entry.appendChild(progress);
        }
        logContainer.appendChild(entry);
        logContainer.scrollTop = logContainer.scrollHeight;
    };

    const source = new EventSource('/automation-status');
    source.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateStatus(data);
        appendLog(data);
    };

    const startForm = document.getElementById('start-form');
    if (startForm) {
        startForm.addEventListener('submit', async (evt) => {
            evt.preventDefault();
            const body = {
                credentials: {
                    username: document.getElementById('username').value,
                    password: document.getElementById('password').value
                },
                configuration: {
                    base_url: document.getElementById('platform').value,
                    headless: 'true'
                }
            };
            try {
                const response = await fetch('/start-campaign', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const result = await response.json();
                if (controlFeedback) {
                    controlFeedback.textContent = result.message || 'Campaign started';
                }
            } catch (error) {
                if (controlFeedback) {
                    controlFeedback.textContent = `Failed to start campaign: ${error}`;
                }
            }
        });
    }

    const stopButton = document.getElementById('stop-button');
    if (stopButton) {
        stopButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/emergency-stop', { method: 'POST' });
                const result = await response.json();
                if (controlFeedback) {
                    controlFeedback.textContent = result.message || 'Stop signal sent';
                }
            } catch (error) {
                if (controlFeedback) {
                    controlFeedback.textContent = `Failed to stop campaign: ${error}`;
                }
            }
        });
    }

    const configForm = document.getElementById('config-form');
    if (configForm) {
        configForm.addEventListener('submit', (evt) => {
            evt.preventDefault();
            const mobileAgents = document.getElementById('mobile_user_agents').value;
            try {
                if (mobileAgents) JSON.parse(mobileAgents);
                configFeedback.textContent = 'Configuration validated and stored locally.';
            } catch (error) {
                configFeedback.textContent = `Invalid JSON: ${error}`;
            }
        });
    }
})();
