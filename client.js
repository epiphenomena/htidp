// client.js

// Helper to check if we are in browser
const isBrowser = typeof window !== 'undefined' && typeof window.document !== 'undefined';

/**
 * Generates a new Ed25519 KeyPair.
 * Uses tweetnacl if available (Browser).
 * @returns {Promise<{publicKey: Uint8Array, secretKey: Uint8Array}>}
 */
async function generateIdentity() {
    if (isBrowser && window.nacl) {
        const keyPair = window.nacl.sign.keyPair();
        return {
            publicKey: keyPair.publicKey,
            secretKey: keyPair.secretKey
        };
    } else {
        throw new Error("Crypto library (nacl) not found. Ensure tweetnacl.js is loaded.");
    }
}

/**
 * Canonicalizes a JSON object (sorts keys recursively).
 * @param {any} obj 
 * @returns {any}
 */
function canonicalize(obj) {
    if (obj === null || typeof obj !== 'object' || Array.isArray(obj)) {
        return obj;
    }
    const sortedKeys = Object.keys(obj).sort();
    const result = {};
    for (const key of sortedKeys) {
        result[key] = canonicalize(obj[key]);
    }
    return result;
}

/**
 * Computes SHA-256 hash of a string (Browser only using SubtleCrypto).
 * @param {string} message 
 * @returns {Promise<Uint8Array>}
 */
async function sha256(message) {
    if (!crypto || !crypto.subtle) {
        throw new Error("Web Crypto API not available.");
    }
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    return new Uint8Array(hashBuffer);
}

/**
 * Creates and signs the handshake request.
 * @param {{publicKey: Uint8Array, secretKey: Uint8Array}} identity 
 * @param {string} introText 
 * @returns {Promise<object>}
 */
async function createSignedHandshakeRequest(identity, introText) {
    if (!window.nacl || !window.nacl.util) {
         throw new Error("nacl.util not found.");
    }

    // 1. Construct payload (without signature)
    // using a temp requester_id
    const payload = {
        requester_id: `https://client.local/${Date.now()}`, 
        timestamp: new Date().toISOString(),
        intro_text: introText,
        public_key: `Ed25519;base64;${window.nacl.util.encodeBase64(identity.publicKey)}`
    };

    // 2. Canonicalize
    const canonicalJson = canonicalize(payload);
    const jsonString = JSON.stringify(canonicalJson);

    // 3. Hash
    const hashBytes = await sha256(jsonString);

    // 4. Sign Hash
    const signatureBytes = window.nacl.sign.detached(hashBytes, identity.secretKey);
    const signatureStr = `Ed25519;base64;${window.nacl.util.encodeBase64(signatureBytes)}`;

    // 5. Add signature
    const finalPayload = {
        ...canonicalJson,
        signature: signatureStr
    };

    return finalPayload;
}

/**
 * Sends the handshake payload to the target URL.
 * @param {string} url 
 * @param {object} payload 
 * @returns {Promise<object>}
 */
async function sendHandshake(url, payload) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        // Try to read error body
        const errorText = await response.text().catch(() => "");
        throw new Error(`Handshake failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    return await response.json();
}

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
        // Clean domain if it contains protocol
        domain = domain.replace(/^https?:\/\//, '');
        
        const wellKnownUrl = `${protocol}${domain}/.well-known/htidp`;
        
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
    module.exports = { discover, generateIdentity, createSignedHandshakeRequest, sendHandshake };
}