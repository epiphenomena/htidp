from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class VCard(BaseModel):
    """
    Standard VCARD information with optional additional fields
    """
    # Standard VCARD fields
    full_name: str = Field(..., description="Full name of the person", min_length=1)
    organization: Optional[str] = Field(None, description="Organization name")
    title: Optional[str] = Field(None, description="Job title")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Physical address")
    website: Optional[HttpUrl] = Field(None, description="Website URL")
    
    # Optional additional fields
    additional_fields: Optional[Dict[str, Any]] = Field(None, description="Additional custom fields")
    
    def to_jcard(self) -> list:
        """
        Convert VCard to jCard format (JSON representation of vCard)
        Returns a list representing the jCard structure
        """
        jcard = ["vcard", []]
        
        # Add required fields
        jcard[1].append(["fn", {}, "text", self.full_name])
        
        # Add optional fields
        if self.organization:
            jcard[1].append(["org", {}, "text", self.organization])
        if self.title:
            jcard[1].append(["title", {}, "text", self.title])
        if self.email:
            jcard[1].append(["email", {}, "text", self.email])
        if self.phone:
            jcard[1].append(["tel", {}, "text", self.phone])
        if self.address:
            jcard[1].append(["adr", {}, "text", self.address])
        if self.website:
            jcard[1].append(["url", {}, "uri", str(self.website)])
            
        return jcard
    
    def to_hcard_html(self) -> str:
        """
        Convert VCard to hCard format (HTML representation of vCard)
        Returns an HTML string with hCard microformat classes
        """
        html = '<div class="vcard">\n'
        html += f'  <span class="fn">{self.full_name}</span>\n'
        
        if self.organization:
            html += f'  <div class="org">{self.organization}</div>\n'
        if self.title:
            html += f'  <div class="title">{self.title}</div>\n'
        if self.email:
            html += f'  <a class="email" href="mailto:{self.email}">{self.email}</a>\n'
        if self.phone:
            html += f'  <div class="tel">{self.phone}</div>\n'
        if self.address:
            html += f'  <div class="adr">{self.address}</div>\n'
        if self.website:
            html += f'  <a class="url" href="{self.website}">{self.website}</a>\n'
            
        html += '</div>'
        return html

class TokenRequest(BaseModel):
    """
    Request for a new link+token
    """
    pass

class TokenResponse(BaseModel):
    """
    Response containing link and token
    """
    link: HttpUrl = Field(..., description="URL to access the contact information")
    token: str = Field(..., description="Token for authentication")

class ExchangeRequest(BaseModel):
    """
    Request sent from one server to another during the exchange process
    """
    token: str = Field(..., description="Token for authentication")
    name: str = Field(..., description="Name or nickname of the requesting party", min_length=1)
    msg: Optional[str] = Field(None, description="Optional message to include with the connection request (max 240 characters)", max_length=240)
    perma_url: HttpUrl = Field(..., description="Permanent URL for the requesting server")
    public_key: str = Field(..., description="Public key for passkey authentication", min_length=1)
    callback_url: HttpUrl = Field(..., description="URL to send response back to")

class ExchangeResponse(BaseModel):
    """
    Response sent back during the exchange process
    """
    token: str = Field(..., description="Token for authentication")
    perma_url: HttpUrl = Field(..., description="Permanent URL for the responding server")
    public_key: str = Field(..., description="Public key for passkey authentication")

class ContactInfoResponse(BaseModel):
    """
    Response containing contact information
    """
    vcard: VCard = Field(..., description="VCARD information")
    last_updated: datetime = Field(..., description="Timestamp of last update")

class HeadResponse(BaseModel):
    """
    Response to HEAD requests indicating if information has changed
    """
    has_changed: bool = Field(..., description="Whether the information has changed since the timestamp")