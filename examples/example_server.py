"""
Example HTIDP server that can be used with the client.html demo
"""
import uvicorn
import argparse
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form
from fastapi.responses import HTMLResponse
import os
from datetime import datetime
from typing import Optional
import vobject

# Create the example app
app = FastAPI(
    title="HTIDP Example Server",
    description="Example server for HTIDP client demo",
    version="1.0.0"
)

# Set up templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Serve static files (including our client.html)
static_dir = os.path.join(os.path.dirname(__file__))
if os.path.exists(static_dir):
    app.mount("/examples", StaticFiles(directory=static_dir), name="examples")

# Simple in-memory storage for demo purposes
contacts = {}
exchanges = {}

# Create a sample vCard for demo purposes
def create_sample_vcard():
    """
    Create a sample vCard for demo purposes
    """
    vcard = vobject.vCard()
    vcard.add('fn')
    vcard.fn.value = "John Doe"
    
    vcard.add('org')
    vcard.org.value = ["Example Corp"]
    
    vcard.add('title')
    vcard.title.value = "Software Engineer"
    
    vcard.add('email')
    vcard.email.value = "john.doe@example.com"
    
    vcard.add('tel')
    vcard.tel.value = "+1-555-123-4567"
    
    vcard.add('adr')
    vcard.adr.value = vobject.vcard.Address(
        street="123 Main St", 
        city="Anytown", 
        code="12345", 
        country="USA"
    )
    
    vcard.add('url')
    vcard.url.value = "https://example.com"
    
    vcard.add('version')
    vcard.version.value = "4.0"
    
    return vcard.serialize()

my_contact_vcard = create_sample_vcard()
my_contact = {
    "id": 1,
    "vcard_data": my_contact_vcard,
    "last_updated": "2025-08-13T10:00:00Z"
}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request
    })

@app.get("/ui/contact", response_class=HTMLResponse)
async def ui_contact_form(request: Request):
    """Web UI for managing contact information"""
    # Parse the vCard to display current values
    vcard = vobject.readOne(my_contact["vcard_data"])

    # Extract values with defaults
    fn = getattr(vcard, 'fn', type('obj', (object,), {'value': ''})()).value
    org = getattr(vcard, 'org', type('obj', (object,), {'value': ['']})()).value[0] if hasattr(vcard, 'org') and vcard.org.value else ''
    title = getattr(vcard, 'title', type('obj', (object,), {'value': ''})()).value if hasattr(vcard, 'title') else ''
    email = getattr(vcard, 'email', type('obj', (object,), {'value': ''})()).value if hasattr(vcard, 'email') else ''
    tel = getattr(vcard, 'tel', type('obj', (object,), {'value': ''})()).value if hasattr(vcard, 'tel') else ''
    adr = getattr(vcard, 'adr', type('obj', (object,), {'value': type('obj', (object,), {'street': ''})()})()).value.street if hasattr(vcard, 'adr') and hasattr(vcard.adr.value, 'street') else ''
    url = getattr(vcard, 'url', type('obj', (object,), {'value': ''})()).value if hasattr(vcard, 'url') else ''
    
    return templates.TemplateResponse("contact_form.html", {
        "request": request,
        "full_name": fn,
        "organization": org,
        "title": title,
        "email": email,
        "phone": tel,
        "address": adr,
        "website": url
    })

@app.post("/ui/contact", response_class=HTMLResponse)
async def ui_update_contact(
    request: Request,
    full_name: str = Form(...),
    organization: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    website: Optional[str] = Form(None)
):
    """Update contact information via web UI"""
    # Create a new vCard
    vcard = vobject.vCard()
    vcard.add('fn')
    vcard.fn.value = full_name
    
    vcard.add('version')
    vcard.version.value = "4.0"
    
    if organization:
        vcard.add('org')
        vcard.org.value = [organization]
    if title:
        vcard.add('title')
        vcard.title.value = title
    if email:
        vcard.add('email')
        vcard.email.value = email
    if phone:
        vcard.add('tel')
        vcard.tel.value = phone
    if address:
        vcard.add('adr')
        # For simplicity, we'll store the address as a single string
        # In a real implementation, you might want to parse this into components
        vcard.adr.value = vobject.vcard.Address(street=address)
    if website:
        vcard.add('url')
        vcard.url.value = website
    
    my_contact["vcard_data"] = vcard.serialize()
    my_contact["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    return templates.TemplateResponse("contact_updated.html", {
        "request": request
    })

@app.get("/ui/contact/view", response_class=HTMLResponse)
async def ui_view_contact(request: Request):
    """View my contact information"""
    # Parse vCard and create hCard HTML
    vcard = vobject.readOne(my_contact["vcard_data"])

    # Create hCard HTML
    hcard_html = '<div class="vcard">\n'
    if hasattr(vcard, 'fn'):
        hcard_html += f'  <span class="fn">{vcard.fn.value}</span>\n'
    if hasattr(vcard, 'org'):
        hcard_html += f'  <div class="org">{vcard.org.value[0]}</div>\n'
    if hasattr(vcard, 'title'):
        hcard_html += f'  <div class="title">{vcard.title.value}</div>\n'
    if hasattr(vcard, 'email'):
        hcard_html += f'  <a class="email" href="mailto:{vcard.email.value}">{vcard.email.value}</a>\n'
    if hasattr(vcard, 'tel'):
        hcard_html += f'  <div class="tel">{vcard.tel.value}</div>\n'
    if hasattr(vcard, 'adr'):
        hcard_html += f'  <div class="adr">{vcard.adr.value.street}</div>\n'
    if hasattr(vcard, 'url'):
        hcard_html += f'  <a class="url" href="{vcard.url.value}">{vcard.url.value}</a>\n'
    hcard_html += '</div>'
    
    return templates.TemplateResponse("contact_view.html", {
        "request": request,
        "vcard_data": my_contact["vcard_data"],
        "last_updated": my_contact["last_updated"],
        "hcard_html": hcard_html
    })

@app.get("/contact/{contact_id}")
async def get_contact(contact_id: str):
    """Get contact information by ID"""
    if contact_id not in contacts:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contacts[contact_id]

@app.post("/contact")
async def create_contact(contact: dict):
    """Create a new contact"""
    contact_id = len(contacts) + 1
    contact["id"] = contact_id
    contacts[contact_id] = contact
    return {"id": contact_id, "message": "Contact created successfully"}

@app.get("/ui/exchange", response_class=HTMLResponse)
async def ui_exchange_form(request: Request):
    """Web UI for initiating contact exchange"""
    return templates.TemplateResponse("exchange_form.html", {
        "request": request
    })

@app.post("/ui/exchange/request", response_class=HTMLResponse)
async def ui_request_exchange(request: Request):
    """Request a contact exchange via web UI"""
    exchange_id = len(exchanges) + 1
    token = f"exchange-token-{exchange_id}"
    exchanges[exchange_id] = {
        "id": exchange_id,
        "token": token,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "unsolicited": False
    }

    return templates.TemplateResponse("token_generated.html", {
        "request": request,
        "header": "Exchange Token Generated",
        "token": token,
        "is_public": False
    })

@app.post("/ui/exchange/public-request", response_class=HTMLResponse)
async def ui_public_request_exchange(request: Request):
    """Request a public contact exchange via web UI"""
    exchange_id = len(exchanges) + 1
    token = f"public-exchange-token-{exchange_id}"
    exchanges[exchange_id] = {
        "id": exchange_id,
        "token": token,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "unsolicited": True
    }

    return templates.TemplateResponse("token_generated.html", {
        "request": request,
        "header": "Public Exchange Token Generated",
        "token": token,
        "is_public": True
    })

@app.post("/ui/exchange/accept", response_class=HTMLResponse)
async def ui_accept_exchange(request: Request, token: str = Form(...)):
    """Accept a contact exchange via web UI"""
    # Find the exchange by token
    exchange = None
    for ex in exchanges.values():
        if ex.get("token") == token:
            exchange = ex
            break

    if not exchange:
        return templates.TemplateResponse("exchange_accept.html", {
            "request": request,
            "error": "Invalid or expired token. Please check the token and try again."
        })

    return templates.TemplateResponse("exchange_accept.html", {
        "request": request,
        "token": token,
        "unsolicited": exchange.get("unsolicited", False)
    })

@app.post("/ui/exchange/submit", response_class=HTMLResponse)
async def ui_submit_exchange(
    request: Request,
    token: str = Form(...),
    your_name: str = Form(...),
    your_msg: Optional[str] = Form(None),
    perma_url: str = Form(...),
    public_key: str = Form(...),
    callback_url: str = Form(...)
):
    """Submit a contact exchange via web UI"""
    # Find the exchange by token
    exchange = None
    for ex in exchanges.values():
        if ex.get("token") == token:
            exchange = ex
            break

    if not exchange:
        return templates.TemplateResponse("exchange_completed.html", {
            "request": request,
            "error": "Invalid or expired token. Please check the token and try again."
        })

    # In a real implementation, we would send the data to the callback URL
    # For this demo, we'll just store the contact
    contact_id = len(contacts) + 1
    # Create a simple vCard for the new contact
    vcard = vobject.vCard()
    vcard.add('fn')
    vcard.fn.value = your_name
    vcard.add('version')
    vcard.version.value = "4.0"

    contacts[contact_id] = {
        "id": contact_id,
        "vcard_data": vcard.serialize(),
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }

    return templates.TemplateResponse("exchange_completed.html", {
        "request": request
    })

@app.post("/exchange")
async def initiate_exchange(exchange: dict):
    """Initiate a contact exchange"""
    exchange_id = len(exchanges) + 1
    exchange["id"] = exchange_id
    exchanges[exchange_id] = exchange
    return {
        "id": exchange_id,
        "message": "Exchange initiated successfully",
        "token": f"exchange-token-{exchange_id}"
    }

@app.get("/exchange/{token}")
async def get_exchange(token: str):
    """Get exchange information by token"""
    # Find the exchange by token
    for ex in exchanges.values():
        if ex.get("token") == token:
            return {
                "post_url": "/exchange/submit",
                "requester_name": ex.get("requester_name", "Unknown User")
            }

    raise HTTPException(status_code=404, detail="Exchange token not found")

@app.post("/exchange/{token}")
async def process_exchange(token: str, exchange_data: dict):
    """Process an exchange request"""
    # Find the exchange by token
    for ex in exchanges.values():
        if ex.get("token") == token:
            # In a real implementation, we would process the exchange
            # For this demo, we'll just return success
            return {"status": "success", "message": "Exchange processed successfully"}

    raise HTTPException(status_code=404, detail="Exchange token not found")

@app.get("/ui/connections", response_class=HTMLResponse)
async def ui_connections(request: Request):
    """Web UI for viewing connections"""
    if not contacts:
        connections_html = "<p>You don't have any connections yet.</p>"
    else:
        connections_html = "<ul>"
        for contact_id, contact in contacts.items():
            # Parse vCard to get name
            try:
                vcard = vobject.readOne(contact["vcard_data"])
                name = vcard.fn.value if hasattr(vcard, 'fn') else f"Contact {contact_id}"
            except:
                name = f"Contact {contact_id}"

            connections_html += f"""
            <li>
                <strong>{name}</strong>
                (ID: {contact_id})
                <a href="/ui/connections/{contact_id}"><button style="margin-left: 10px;">View</button></a>
            </li>
            """
        connections_html += "</ul>"

    # Add section for unsolicited connections
    unsolicited_notice = ""
    unsolicited_exchanges = [ex for ex in exchanges.values() if ex.get("unsolicited")]
    if unsolicited_exchanges:
        unsolicited_notice = True

    return templates.TemplateResponse("connections.html", {
        "request": request,
        "connections_html": connections_html,
        "unsolicited_notice": unsolicited_notice
    })

@app.get("/ui/connections/{contact_id}", response_class=HTMLResponse)
async def ui_view_connection(request: Request, contact_id: int):
    """View a specific connection"""
    if str(contact_id) not in contacts:
        return templates.TemplateResponse("connection_view.html", {
            "request": request,
            "error": "The requested connection was not found."
        })

    contact = contacts[str(contact_id)]

    # Parse vCard and create hCard HTML
    try:
        vcard = vobject.readOne(contact["vcard_data"])

        # Create hCard HTML
        hcard_html = '<div class="vcard">\n'
        if hasattr(vcard, 'fn'):
            hcard_html += f'  <span class="fn">{vcard.fn.value}</span>\n'
        if hasattr(vcard, 'org'):
            hcard_html += f'  <div class="org">{vcard.org.value[0]}</div>\n'
        if hasattr(vcard, 'title'):
            hcard_html += f'  <div class="title">{vcard.title.value}</div>\n'
        if hasattr(vcard, 'email'):
            hcard_html += f'  <a class="email" href="mailto:{vcard.email.value}">{vcard.email.value}</a>\n'
        if hasattr(vcard, 'tel'):
            hcard_html += f'  <div class="tel">{vcard.tel.value}</div>\n'
        if hasattr(vcard, 'adr'):
            hcard_html += f'  <div class="adr">{vcard.adr.value.street}</div>\n'
        if hasattr(vcard, 'url'):
            hcard_html += f'  <a class="url" href="{vcard.url.value}">{vcard.url.value}</a>\n'
        hcard_html += '</div>'
    except:
        hcard_html = "<p>Error parsing contact information.</p>"

    return templates.TemplateResponse("connection_view.html", {
        "request": request,
        "vcard_data": contact["vcard_data"],
        "last_updated": contact["last_updated"],
        "hcard_html": hcard_html
    })

@app.head("/contact/{contact_id}")
async def check_contact_update(contact_id: str, request: Request):
    """Check if contact information has been updated"""
    if contact_id not in contacts:
        raise HTTPException(status_code=404, detail="Contact not found")

    response = JSONResponse(content={})
    response.headers["Last-Modified"] = "Wed, 21 Oct 2025 07:28:00 GMT"
    return response

def main():
    parser = argparse.ArgumentParser(description="HTIDP Example Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    uvicorn.run(
        "examples.example_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()