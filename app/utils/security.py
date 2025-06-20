"""
Security utilities for authentication, authorization, and data protection.
"""

import hashlib
import secrets
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import jwt

logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Security manager for handling authentication and authorization.
    """
    
    def __init__(self, secret_key: str = None):
        """Initialize security manager."""
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.logger = logger
        
        # Token blacklist for logout functionality
        self.blacklisted_tokens = set()
    
    def generate_api_key(self, prefix: str = "rma") -> str:
        """Generate a secure API key."""
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key
    
    def generate_jwt_token(
        self,
        payload: Dict[str, Any],
        expires_in: int = 3600
    ) -> str:
        """Generate a JWT token."""
        now = datetime.now(timezone.utc)
        payload.update({
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
            "jti": secrets.token_urlsafe(16)  # JWT ID for blacklisting
        })
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            # Check if token is blacklisted
            if token in self.blacklisted_tokens:
                return None
            
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid JWT token")
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """Blacklist a JWT token (for logout)."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            self.blacklisted_tokens.add(token)
            return True
        except jwt.InvalidTokenError:
            return False
    
    def cleanup_blacklist(self) -> int:
        """Remove expired tokens from blacklist."""
        current_time = datetime.now(timezone.utc)
        expired_tokens = []
        
        for token in self.blacklisted_tokens:
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
                exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
                if current_time > exp_time:
                    expired_tokens.append(token)
            except jwt.InvalidTokenError:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            self.blacklisted_tokens.discard(token)
        
        return len(expired_tokens)


class DataSanitizer:
    """
    Data sanitization utilities for preventing injection attacks.
    """
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        if not filename:
            return "unnamed"
        
        # Remove path separators and dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        sanitized = filename
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "unnamed"
        
        return sanitized[:255]  # Limit filename length
    
    @staticmethod
    def validate_organization_id(org_id: str) -> bool:
        """Validate organization ID format."""
        if not org_id or not isinstance(org_id, str):
            return False
        
        # Allow alphanumeric, hyphens, and underscores only
        import re
        pattern = r'^[a-zA-Z0-9_-]{3,50}$'
        return bool(re.match(pattern, org_id))
    
    @staticmethod
    def sanitize_reddit_credentials(creds: Dict[str, Any]) -> Dict[str, str]:
        """Sanitize Reddit API credentials."""
        sanitized = {}
        
        required_fields = ["client_id", "client_secret"]
        optional_fields = ["username", "password", "user_agent"]
        
        for field in required_fields:
            if field in creds and isinstance(creds[field], str):
                sanitized[field] = DataSanitizer.sanitize_string(creds[field], 100)
        
        for field in optional_fields:
            if field in creds and isinstance(creds[field], str):
                sanitized[field] = DataSanitizer.sanitize_string(creds[field], 200)
        
        return sanitized


class AuditLogger:
    """
    Audit logging for security-sensitive operations.
    """
    
    def __init__(self):
        """Initialize audit logger."""
        self.logger = logging.getLogger("audit")
        self.audit_events = []
    
    def log_event(
        self,
        event_type: str,
        user_id: str = None,
        organization_id: str = None,
        resource: str = None,
        action: str = None,
        details: Dict[str, Any] = None,
        success: bool = True
    ):
        """Log an audit event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "organization_id": organization_id,
            "resource": resource,
            "action": action,
            "details": details or {},
            "success": success
        }
        
        self.audit_events.append(event)
        
        # Log to file
        self.logger.info(f"AUDIT: {event_type} - {action} on {resource} by {user_id} - {'SUCCESS' if success else 'FAILED'}")
    
    def get_audit_trail(
        self,
        user_id: str = None,
        organization_id: str = None,
        event_type: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail with optional filters."""
        filtered_events = self.audit_events
        
        if user_id:
            filtered_events = [e for e in filtered_events if e.get("user_id") == user_id]
        
        if organization_id:
            filtered_events = [e for e in filtered_events if e.get("organization_id") == organization_id]
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.get("event_type") == event_type]
        
        return filtered_events[-limit:]


class RateLimitManager:
    """
    Advanced rate limiting with different strategies.
    """
    
    def __init__(self):
        """Initialize rate limit manager."""
        self.limits = {}
        self.logger = logger
    
    def set_limit(
        self,
        identifier: str,
        max_requests: int,
        time_window: int,
        strategy: str = "sliding_window"
    ):
        """Set rate limit for identifier."""
        self.limits[identifier] = {
            "max_requests": max_requests,
            "time_window": time_window,
            "strategy": strategy,
            "requests": []
        }
    
    def check_limit(self, identifier: str) -> tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limit."""
        if identifier not in self.limits:
            return True, {"remaining": float('inf'), "reset_time": None}
        
        limit_config = self.limits[identifier]
        current_time = datetime.now(timezone.utc).timestamp()
        
        # Clean old requests
        time_window = limit_config["time_window"]
        limit_config["requests"] = [
            req_time for req_time in limit_config["requests"]
            if current_time - req_time < time_window
        ]
        
        # Check limit
        current_requests = len(limit_config["requests"])
        max_requests = limit_config["max_requests"]
        
        if current_requests < max_requests:
            limit_config["requests"].append(current_time)
            remaining = max_requests - current_requests - 1
            reset_time = current_time + time_window
            return True, {"remaining": remaining, "reset_time": reset_time}
        else:
            oldest_request = min(limit_config["requests"]) if limit_config["requests"] else current_time
            reset_time = oldest_request + time_window
            return False, {"remaining": 0, "reset_time": reset_time}


# Global instances
security_manager = SecurityManager()
data_sanitizer = DataSanitizer()
audit_logger = AuditLogger()
rate_limit_manager = RateLimitManager()