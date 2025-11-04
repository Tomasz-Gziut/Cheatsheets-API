from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from firebase_admin.firestore import FieldFilter

from config import db
from auth import create_token, verify_password
from schemas import UserLogin

router = APIRouter(tags=["auth"])

@router.post("/login")
def login(credentials: UserLogin):
    try:
        users = db.collection("users").where(filter=FieldFilter("login", "==", credentials.login)).stream()
        user_doc = None
        for doc in users:
            user_doc = doc
            break
        
        if not user_doc:
            raise HTTPException(status_code=401, detail="Invalid login or password")
        
        user_data = user_doc.to_dict()
        if not verify_password(credentials.password, user_data["password"]):
            raise HTTPException(status_code=401, detail="Invalid login or password")
        
        user_type = user_data.get("type", "none")
        token = create_token(user_doc.id, user_type)
        
        created_at = user_data.get("created_at")
        response_data = {
            "id": user_doc.id,
            "login": user_data["login"],
            "type": user_type,
            "created_at": created_at.isoformat() if created_at else None
        }
        
        response = JSONResponse(content=response_data)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
def logout():
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(
        key="access_token",
        secure=True,
        httponly=True,
        samesite="lax"
    )
    return response
