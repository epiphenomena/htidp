// client.js

/**
 * Discovers the handshake URL for a given domain using HTIDP discovery flow.
 *
 * @param {string} domain - The domain to discover (e.g., "alice.com" or "localhost:8080").
 * @returns {Promise<string>} - The handshake URL.
 * @throws {Error} - If discovery fails.
 */
async function discover(domain) {
    try {
        // Construct the well-known URL.
        // If domain doesn't start with http, assume https unless it's localhost (dev mode).
        let protocol = 'https://';
        if (domain.startsWith('localhost') || domain.includes(':')) {
            protocol = 'http://';
        }
        // If the user provided a full URL, strip protocol for the well-known construction or handle smarter.
        // For this task, we assume 'domain' is a hostname like "alice.com".
        
        const wellKnownUrl = `${protocol}${domain}/.well-known/htidp`;
        
        // Note: In a real browser environment, if 'domain' is not the origin, CORS must be enabled on the server.
        // We assume the server allows '*'.
        
        console.log(`Fetching ${wellKnownUrl}...`);
        const wellKnownResponse = await fetch(wellKnownUrl).catch(err => {
            // Handle network errors (including potential CORS blocks that look like network errors)
            throw new Error(`Network error fetching ${wellKnownUrl}: ${err.message}`);
        });
        
        if (!wellKnownResponse.ok) {
            throw new Error(`Failed to fetch ${wellKnownUrl}: ${wellKnownResponse.status} ${wellKnownResponse.statusText}`);
        }

        const wellKnownData = await wellKnownResponse.json();
        const apiRoot = wellKnownData.api_root;

        if (!apiRoot) {
            throw new Error(`Invalid response from ${wellKnownUrl}: missing 'api_root'`);
        }

        console.log(`Discovered API root: ${apiRoot}`);

        // Step 2: Fetch API Root to find handshake link
        const apiRootResponse = await fetch(apiRoot).catch(err => {
             throw new Error(`Network error fetching API root ${apiRoot}: ${err.message}`);
        });

        if (!apiRootResponse.ok) {
            throw new Error(`Failed to fetch API root ${apiRoot}: ${apiRootResponse.status} ${apiRootResponse.statusText}`);
        }

        const apiRootData = await apiRootResponse.json();

        if (!apiRootData.links || !Array.isArray(apiRootData.links)) {
             throw new Error(`Invalid response from ${apiRoot}: missing or invalid 'links' array`);
        }

        const handshakeLink = apiRootData.links.find(link => link.rel === 'handshake');

        if (!handshakeLink || !handshakeLink.href) {
            throw new Error(`No handshake link found in API root ${apiRoot}`);
        }

        console.log(`Found handshake URL: ${handshakeLink.href}`);
        return handshakeLink.href;

    } catch (error) {
        console.error("Discovery failed:", error);
        throw error;
    }
}

// Export for Node.js/Test environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { discover };
}
