// profile.js

async function fetchFromAdmin(path, options = {}) {
    const baseUrl = document.getElementById('server-url').value.replace(/\/$/, '');
    const response = await fetch(`${baseUrl}${path}`, options);
    if (!response.ok) {
        throw new Error(`Admin API error: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

async function loadIdentity() {
    const identityDiv = document.getElementById('identity-card');
    try {
        const baseUrl = document.getElementById('server-url').value.replace(/\/$/, '');
        const response = await fetch(`${baseUrl}/api/v1/identity`);
        if (!response.ok) throw new Error("Could not fetch identity");
        
        const profile = await response.json();
        const fn = profile["https://htidp.org/core/vcard#fn"] || "Unknown";
        const note = profile["https://htidp.org/core/vcard#note"] || "No bio available.";
        const photo = profile["https://htidp.org/core/vcard#photo"] || "";

        identityDiv.innerHTML = `
            <strong>Name:</strong> ${fn}<br>
            <strong>Bio:</strong> ${note}<br>
            ${photo ? `<img src="${photo}" alt="Profile" style="width: 50px; height: 50px; display: block; margin-top: 0.5rem; border-radius: 4px;">` : ''}
        `;
    } catch (err) {
        identityDiv.innerHTML = `<span class="error">Failed to load identity: ${err.message}</span>`;
    }
}

async function loadPending() {
    const listDiv = document.getElementById('pending-list');
    try {
        const requests = await fetchFromAdmin('/admin/requests');
        if (requests.length === 0) {
            listDiv.innerHTML = '<p class="empty">No pending requests.</p>';
            return;
        }

        listDiv.innerHTML = requests.map(req => `
            <div class="card">
                <div>
                    <span class="requester">${req.RequesterID}</span>
                    <span class="badge badge-pending">Pending</span>
                </div>
                <div class="timestamp">${new Date(req.Timestamp).toLocaleString()}</div>
                <div class="intro">"${req.IntroText}"</div>
                <div class="actions">
                    <button class="approve" onclick="approveRequest('${req.ID}')">Approve Connection</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        listDiv.innerHTML = `<p class="error">${err.message}</p>`;
    }
}

async function loadActive() {
    const listDiv = document.getElementById('active-list');
    try {
        const connections = await fetchFromAdmin('/admin/active');
        if (connections.length === 0) {
            listDiv.innerHTML = '<p class="empty">No established connections yet.</p>';
            return;
        }

        listDiv.innerHTML = connections.map(conn => `
            <div class="card">
                <div>
                    <span class="requester">${conn.RequesterID}</span>
                    <span class="badge badge-active">Active</span>
                </div>
                <div class="intro">Shared Token: <span class="token">${conn.AccessToken}</span></div>
                ${conn.LinkedTo ? `<div class="timestamp">Delegated by: ${conn.LinkedTo}</div>` : ''}
            </div>
        `).join('');
    } catch (err) {
        listDiv.innerHTML = `<p class="error">${err.message}</p>`;
    }
}

async function approveRequest(id) {
    try {
        await fetchFromAdmin(`/admin/approve/${id}`, { method: 'POST' });
        alert('Connection Approved!');
        loadData();
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}

function loadData() {
    loadIdentity();
    loadPending();
    loadActive();
}

// Initial load
loadData();
