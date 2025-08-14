# HTIDP - HyperText ID Protocol Implementation

This is a Python/FastAPI implementation of the HTIDP (HyperText ID Protocol).

## Features

- RESTful API for sharing contact information
- Token-based exchange mechanism
- VCARD standard compliance with optional additional fields
- Passkey authentication for secure information exchange
- Content negotiation (HTML/JSON) based on Accept headers
- XSS protection through template escaping
- CORS support

## Installation

### Using uv (recommended)

1. Clone the repository:
   ```
   git clone <repository-url>
   cd htidp
   ```

2. Install [uv](https://github.com/astral-sh/uv) if you haven't already:
   ```
   pip install uv
   ```

3. Install dependencies:
   ```
   uv sync
   ```

### Using pip

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
   pip install -e .
   ```

## Running the Application

### Development Mode

```
uv run htidp-server --reload
```

Or using the module directly:
```
python -m app.server --reload
```

### Production Mode

```
uv run htidp-server
```

Or using the module directly:
```
python -m app.server
```

The server will start on `http://127.0.0.1:8000` by default.

## API Endpoints

- `POST /request-token` - Request a new link+token for sharing contact information
- `GET /exchange/{token}` - Get exchange information for a token
- `POST /exchange/{token}` - Process the exchange of contact information between servers
- `GET /contact/{contact_id}` - Get contact information with passkey challenge
- `HEAD /contact/{contact_id}` - Check if contact information has changed since a timestamp
- `GET /health` - Health check endpoint

## Examples

The `examples/` directory contains:

1. A standalone HTML/JavaScript client demo (`client.html`)
2. An example server implementation (`example_server.py`)

See [examples/README.md](examples/README.md) for details on how to run the examples.

## Testing

To run tests:

```
uv run pytest
```

Or using pip installation:
```
pip install -e .[test]
pytest
```

## Configuration

The application can be configured using the `config.ini` file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.