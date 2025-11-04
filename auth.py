import datetime
import jwt
import bcrypt
from typing import Optional
from fastapi import HTTPException, Header, Cookie

from config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_HOURS

def create_token(user_id: str, user_type: str) -> str:
    payload = {
        "sub": user_id,
        "type": user_type,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: Optional[str] = Header(None), access_token: Optional[str] = Cookie(None)) -> Optional[dict]:
    token = None
    
    if access_token:
        token = access_token
    elif authorization:
        try:
            token = authorization.split(" ")[1]
        except:
            pass
    
    if not token:
        return None
    
    try:
        payload = verify_token(token)
        return {"id": payload["sub"], "type": payload["type"]}
    except:
        return None

async def require_auth(authorization: Optional[str] = Header(None), access_token: Optional[str] = Cookie(None)) -> dict:
    token = None
    
    if access_token:
        token = access_token
    elif authorization:
        try:
            token = authorization.split(" ")[1]
        except:
            pass
    
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header or token cookie")
    
    try:
        payload = verify_token(token)
        return {"id": payload["sub"], "type": payload["type"]}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(current_user: dict) -> dict:
    if current_user["type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())
