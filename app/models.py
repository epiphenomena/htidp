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

class TokenRequest(BaseModel):
    """
    Request for a new link+token
    """
    msg: Optional[str] = Field(None, description="Optional message to include with the token (max 240 characters)", max_length=240)

class TokenResponse(BaseModel):
    """
    Response containing link and token
    """
    link: HttpUrl = Field(..., description="URL to access the contact information")
    token: str = Field(..., description="Token for authentication")
    msg: Optional[str] = Field(None, description="Optional message included with the token")

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