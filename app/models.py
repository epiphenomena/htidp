from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import vobject


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
    vcard_data: str = Field(..., description="Raw vCard data as string")
    last_updated: datetime = Field(..., description="Timestamp of last update")
    
    @property
    def vcard(self):
        """
        Parse and return vCard object
        """
        return vobject.readOne(self.vcard_data)
    
    def to_jcard(self):
        """
        Convert to jCard format
        """
        vcard = self.vcard
        jcard = ["vcard", []]
        
        # Add all vCard properties to jCard
        for prop in vcard.getChildren():
            if prop.name == "VERSION":
                continue  # Skip VERSION property in jCard
            
            # Handle different property types
            if hasattr(prop, 'value'):
                if isinstance(prop.value, list):
                    value = prop.value
                else:
                    value = str(prop.value)
            else:
                value = ""
                
            jcard[1].append([prop.name.lower(), {}, "text", value])
            
        return jcard
    
    def to_hcard_html(self):
        """
        Convert to hCard formatted HTML
        """
        vcard = self.vcard
        html = '<div class="vcard">\n'
        
        # Map common vCard properties to hCard classes
        property_map = {
            'FN': 'fn',
            'N': 'n',
            'ORG': 'org',
            'TITLE': 'title',
            'EMAIL': 'email',
            'TEL': 'tel',
            'ADR': 'adr',
            'URL': 'url'
        }
        
        # Add all vCard properties to HTML
        for prop in vcard.getChildren():
            prop_name = prop.name
            hcard_class = property_map.get(prop_name, prop_name.lower())
            
            if hasattr(prop, 'value'):
                if isinstance(prop.value, list):
                    value = ', '.join(str(v) for v in prop.value)
                else:
                    value = str(prop.value)
            else:
                value = ""
            
            if prop_name == "EMAIL":
                html += f'  <a class="{hcard_class}" href="mailto:{value}">{value}</a>\n'
            elif prop_name == "URL":
                html += f'  <a class="{hcard_class}" href="{value}">{value}</a>\n'
            else:
                html += f'  <span class="{hcard_class}">{value}</span>\n'
                
        html += '</div>'
        return html


class HeadResponse(BaseModel):
    """
    Response to HEAD requests indicating if information has changed
    """
    has_changed: bool = Field(..., description="Whether the information has changed since the timestamp")