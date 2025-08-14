import uuid
from datetime import datetime
from typing import Dict, Optional
from fastapi import HTTPException
from .models import TokenResponse, VCard, ContactInfoResponse, ExchangeRequest

class HTIDPService:
    """
    Core service for HTIDP implementation
    """
    
    def __init__(self):
        # In-memory storage for demonstration
        # In production, this would be a database
        self.tokens: Dict[str, dict] = {}
        self.contacts: Dict[str, dict] = {}
        self.connections: Dict[str, dict] = {}  # Store connections between parties
        
    def generate_token(self, msg: Optional[str] = None) -> TokenResponse:
        """
        Generate a new link+token for sharing contact information
        """
        token = str(uuid.uuid4())
        link = f"https://example.com/exchange/{token}"
        
        self.tokens[token] = {
            "msg": msg,
            "created_at": datetime.utcnow(),
            "used": False,
            "unsolicited": False  # Track if this was a public/unsolicited request
        }
        
        return TokenResponse(
            link=link,
            token=token,
            msg=msg
        )
        
    def generate_public_token(self, msg: Optional[str] = None) -> TokenResponse:
        """
        Generate a new link+token for public/unsolicited sharing
        """
        token = str(uuid.uuid4())
        link = f"https://example.com/public-exchange/{token}"
        
        self.tokens[token] = {
            "msg": msg,
            "created_at": datetime.utcnow(),
            "used": False,
            "unsolicited": True  # Mark as public/unsolicited request
        }
        
        return TokenResponse(
            link=link,
            token=token,
            msg=msg
        )
        
    def validate_token(self, token: str) -> Optional[dict]:
        """
        Validate a token and return its information
        """
        if token not in self.tokens:
            return None
            
        token_info = self.tokens[token]
        if token_info["used"]:
            return None
            
        return token_info
        
    def mark_token_used(self, token: str):
        """
        Mark a token as used
        """
        if token in self.tokens:
            self.tokens[token]["used"] = True
            
    def store_contact_info(self, contact_id: str, vcard: VCard):
        """
        Store contact information
        """
        self.contacts[contact_id] = {
            "vcard": vcard,
            "last_updated": datetime.utcnow()
        }
        
    def get_contact_info(self, contact_id: str) -> Optional[ContactInfoResponse]:
        """
        Retrieve contact information
        """
        if contact_id not in self.contacts:
            return None
            
        contact = self.contacts[contact_id]
        return ContactInfoResponse(
            vcard=contact["vcard"],
            last_updated=contact["last_updated"]
        )
        
    def process_exchange(self, token: str, exchange_request: ExchangeRequest) -> bool:
        """
        Process the exchange of contact information between servers
        """
        token_info = self.validate_token(token)
        if not token_info:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
            
        # Create a connection ID
        connection_id = str(uuid.uuid4())
        
        # Store the connection information
        self.connections[connection_id] = {
            "token": token,
            "requester_name": exchange_request.name,
            "requester_msg": exchange_request.msg,
            "requester_url": str(exchange_request.perma_url),
            "requester_public_key": exchange_request.public_key,
            "callback_url": str(exchange_request.callback_url),
            "created_at": datetime.utcnow(),
            "unsolicited": token_info.get("unsolicited", False)
        }
        
        # Mark token as used
        self.mark_token_used(token)
        return True
        
    def get_connection_info(self, token: str) -> Optional[dict]:
        """
        Get connection information for a token
        """
        # Find connection by token
        for connection_id, connection in self.connections.items():
            if connection["token"] == token:
                token_info = self.tokens.get(token, {})
                return {
                    "post_url": f"/exchange/{token}",
                    "requester_name": connection["requester_name"],
                    "requester_msg": connection.get("requester_msg"),
                    "unsolicited": connection.get("unsolicited", False)
                }
        return None

# Global service instance
htidp_service = HTIDPService()