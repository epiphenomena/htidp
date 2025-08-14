# HTIDP - HyperText ID Protocol Implementation

This is a Python/FastAPI implementation of the HTIDP (HyperText ID Protocol) Version 1.

## Features

- RESTful API for sharing contact information
- Token-based exchange mechanism
- VCARD standard compliance with optional additional fields
- Passkey authentication for secure information exchange
- Content negotiation (HTML/JSON) based on Accept headers
- XSS protection through template escaping
- CORS support

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd htidp
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

### Development Mode

```
python -m app.server --reload
```

### Production Mode

```
python -m app.server
```

The server will start on `http://127.0.0.1:8000` by default.

## API Endpoints

- `POST /v1/request-token` - Request a new link+token for sharing contact information
- `GET /v1/exchange/{token}` - Get exchange information for a token
- `POST /v1/exchange/{token}` - Process the exchange of contact information between servers
- `GET /v1/contact/{contact_id}` - Get contact information with passkey challenge
- `HEAD /v1/contact/{contact_id}` - Check if contact information has changed since a timestamp
- `GET /v1/health` - Health check endpoint

## Examples

The `examples/` directory contains:

1. A standalone HTML/JavaScript client demo (`client.html`)
2. An example server implementation (`example_server.py`)

See [examples/README.md](examples/README.md) for details on how to run the examples.

## Testing

To run tests:

```
pip install -r tests/requirements.txt
pytest
```

## Configuration

The application can be configured using the `config.ini` file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.