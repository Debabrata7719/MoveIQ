from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from api.auth.jwt_handler import decode_access_token
from database.sql_utils import get_user_roles
import json

security = HTTPBearer()

def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Decodes the JWT token from the Authorization header, validates the session in Redis,
    performs IP and User-Agent fingerprinting, and returns the user data.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject (user_id)",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Validate against Redis Session
    session_key = f"session:{token}"
    try:
        from database.redis_utils import get_redis_client
        r_client = get_redis_client()
        raw_session = r_client.get(session_key)
        
        if not raw_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired or logged out",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        session_data = json.loads(raw_session)
        
        # Verify IP and User-Agent with adaptive risk rules
        current_ip = request.client.host if request.client else "unknown"
        current_ua = request.headers.get("user-agent", "unknown")
        
        from api.auth.geo_utils import get_country_from_ip
        current_country = get_country_from_ip(current_ip)
        
        stored_ua = session_data.get("user_agent")
        stored_country = session_data.get("country")
        
        # Risk assessment: User-Agent change OR Country Code change constitutes High Risk
        is_user_agent_changed = stored_ua != current_ua
        is_country_changed = stored_country and current_country and stored_country != current_country
        
        if is_user_agent_changed or is_country_changed:
            # High Risk: Revoke hijacked session immediately
            r_client.delete(session_key)
            try:
                from src.worker.notification_tasks import send_security_alert_email_task
                email = payload.get("email") or session_data.get("email")
                if email:
                    send_security_alert_email_task.apply_async(args=[email, current_ua, current_ip], queue="default")
            except Exception as email_err:
                print(f"Failed to queue security email: {email_err}")
                
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="abnormal_device_change",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Low Risk: IP changed but same browser & same country -> update IP and slide session
        if session_data.get("ip") != current_ip:
            session_data["ip"] = current_ip
            raw_session = json.dumps(session_data)
            
        # Slide/renew session expiration
        remember_me = session_data.get("remember_me", False)
        ttl = 30 * 24 * 3600 if remember_me else 3600
        r_client.setex(session_key, ttl, raw_session)
        
    except HTTPException:
        raise
    except Exception as e:
        # Fallback to standard stateless JWT validation if Redis connection fails
        print(f"Redis session validation fallback: {e}")
        
    # Optional: fetch roles directly from JWT if embedded, or query MySQL
    roles = payload.get("roles")
    if not roles:
        roles = get_user_roles(int(user_id))
        
    return {
        "user_id": str(user_id),
        "email": payload.get("email"),
        "roles": roles
    }


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Restricts access to users carrying the internal ops role. Returns 403 silently."""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return current_user
