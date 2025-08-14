from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from ..models import (
    TokenRequest, TokenResponse, ExchangeRequest, 
    ContactInfoResponse
)
from ..service import htidp_service
import vobject
import json

# Set up templates
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

@router.post("/request-token", response_model=TokenResponse)
async def request_token(token_request: TokenRequest):
    """
    Request a new link+token for sharing contact information (authenticated user)
    """
    return htidp_service.generate_token()

@router.post("/public-request-token", response_model=TokenResponse)
async def public_request_token(token_request: TokenRequest):
    """
    Request a new link+token for public/unsolicited sharing
    This endpoint can be used by anyone to request a connection,
    such as for QR codes at conferences or website "Connect" links.
    """
    return htidp_service.generate_public_token()

@router.get("/exchange/{token}")
async def get_exchange_info(request: Request, token: str, accept: str = Header(default="*/*")):
    """
    Get exchange information for a token
    This endpoint returns either HTML or JSON based on the Accept header:
    - application/json or */*: Returns JSON with URL to POST and requester information
    - text/html: Returns an HTML form for manual exchange
    """
    # First check if this is a valid, unused token
    token_info = htidp_service.validate_token(token)
    if not token_info:
        # Check if this token was already used and has connection_info
        connection_info = htidp_service.get_connection_info(token)
        if connection_info:
            # For already used tokens, still do content negotiation
            if "text/html" in accept:
                return templates.TemplateResponse(
                    request=request,
                    name="exchange_used.html",
                    context={
                        "requester_name": connection_info["requester_name"],
                        "requester_msg": connection_info.get("requester_msg"),
                        "unsolicited": connection_info.get("unsolicited", False)
                    }
                )
            else:
                return connection_info
        raise HTTPException(status_code=404, detail="Token not found or expired")
    
    # Return appropriate response based on Accept header
    if "text/html" in accept:
        # Return HTML form
        return templates.TemplateResponse(
            request=request,
            name="exchange.html",
            context={
                "token": token,
                "unsolicited": token_info.get("unsolicited", False)
            }
        )
    else:
        # Return JSON response (default)
        return {
            "post_url": f"/exchange/{token}"
        }

@router.post("/exchange/{token}")
async def process_exchange(token: str, exchange_request: ExchangeRequest):
    """
    Process the exchange of contact information between servers
    """
    # Verify the token in the request matches the path parameter
    if exchange_request.token != token:
        raise HTTPException(status_code=400, detail="Token mismatch")
        
    try:
        # Process the exchange
        result = htidp_service.process_exchange(token, exchange_request)
        
        if result:
            # In a real implementation, we would send our information
            # to the callback URL
            return {"status": "success", "message": "Exchange completed"}
        else:
            raise HTTPException(status_code=400, detail="Exchange failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/contact/{contact_id}", response_model=ContactInfoResponse)
async def get_contact_info(request: Request, contact_id: str, accept: str = Header(default="*/*")):
    """
    Get contact information with passkey challenge
    Returns either HTML or JSON based on Accept header.
    """
    contact_info = htidp_service.get_contact_info(contact_id)
    if not contact_info:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Check if client specifically requested jCard format
    if "application/vcard+json" in accept:
        # Return jCard format
        jcard = contact_info.to_jcard()
        return JSONResponse(content=jcard)
    
    # Check if client specifically requested vCard format
    if "text/vcard" in accept:
        # Return vCard format
        return Response(content=contact_info.vcard_data, media_type="text/vcard")
    
    # For demonstration, we'll return the same data in both formats
    # In a real implementation, HTML might show a user-friendly view
    if "text/html" in accept:
        # Return hCard formatted HTML
        hcard_html = contact_info.to_hcard_html()
        return templates.TemplateResponse(
            request=request,
            name="contact.html",
            context={
                "vcard_data": contact_info.vcard_data,
                "last_updated": contact_info.last_updated,
                "hcard_html": hcard_html
            }
        )
    else:
        # Return JSON response (default) - still return our ContactInfoResponse
        # but client can also request jCard format specifically
        return contact_info

@router.head("/contact/{contact_id}")
async def check_contact_update(contact_id: str, request: Request):
    """
    Check if contact information has changed since a timestamp
    """
    # In a real implementation, we would:
    # 1. Extract timestamp from headers
    # 2. Decrypt it with the public key
    # 3. Compare with last updated time
    # 4. Return appropriate headers indicating changes
    
    contact_info = htidp_service.get_contact_info(contact_id)
    if not contact_info:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # For demonstration, we'll just return headers indicating
    # the resource exists
    response = JSONResponse(content={})
    response.headers["Last-Modified"] = contact_info.last_updated.isoformat()
    return response

# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}