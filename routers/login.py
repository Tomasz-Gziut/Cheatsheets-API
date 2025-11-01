from fastapi import APIRouter, HTTPException
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
        
        return {
            "id": user_doc.id,
            "login": user_data["login"],
            "type": user_type,
            "token": token,
            "created_at": user_data.get("created_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
