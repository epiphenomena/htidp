# HTIDP Examples

This directory contains example implementations and demonstrations of the HTIDP protocol.

## Client Demo

The `client.html` file is a standalone HTML/JavaScript client that demonstrates how to interact with the HTIDP API. It provides a user interface for:

1. Generating exchange tokens
2. Accepting exchange requests
3. Viewing contact information

To use the client demo:

1. Start the main HTIDP server: `python -m app.server`
2. Open `client.html` in a web browser
3. Use the interface to generate tokens and exchange contact information

## Example Server

The `example_server.py` file provides a simple server implementation that can be used with the client demo. It implements the basic endpoints needed for HTIDP communication.

To run the example server:

```bash
python -m examples.example_server
```

The server will start on http://127.0.0.1:8001 by default.

## Web-based UI

The example server now includes a comprehensive web-based UI that allows users to:

1. **Manage Contact Information** (`/ui/contact`)
   - Create and update your own contact details
   - View your current contact information

2. **Exchange Contacts** (`/ui/exchange`)
   - Generate tokens to share your contact information
   - Accept tokens from others to exchange contact details

3. **View Connections** (`/ui/connections`)
   - See a list of all your exchanged contacts
   - View detailed information for each connection

To use the web-based UI, simply navigate to the root URL of the example server (http://127.0.0.1:8001) and use the provided links to access the different features.

## Usage

1. Start the main HTIDP server:
   ```bash
   python -m app.server
   ```

2. In another terminal, start the example server:
   ```bash
   python -m examples.example_server
   ```

3. Access the web-based UI at http://127.0.0.1:8001

4. Alternatively, open `client.html` in a web browser to interact with the APIs using the standalone client

Note: The example implementations are for demonstration purposes only and do not include full security features that would be required in a production environment.