const { discover } = require('./client.js');
const assert = require('assert');

async function testDiscover() {
    try {
        const domain = 'localhost:8081';
        console.log(`Testing discover("${domain}")...`);
        const handshakeUrl = await discover(domain);
        console.log('Result:', handshakeUrl);
        
        const expected = `http://${domain}/api/v1/handshake`;
        assert.strictEqual(handshakeUrl, expected, `Expected ${expected}, got ${handshakeUrl}`);
        
        console.log('Test Passed!');
    } catch (error) {
        console.error('Test Failed:', error);
        process.exit(1);
    }
}

testDiscover();