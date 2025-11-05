import datetime
from fastapi import APIRouter, HTTPException, Depends
from firebase_admin.firestore import FieldFilter

from config import db
from auth import require_admin, hash_password
from schemas import UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
def list_users(current_user: dict = Depends(require_admin)):
    try:
        users = []
        for doc in db.collection("users").stream():
            user_data = doc.to_dict()
            if "created_at" in user_data and user_data["created_at"]:
                user_data["created_at"] = user_data["created_at"].strftime("%Y-%m-%dT%H:%M")
            if "updated_at" in user_data and user_data["updated_at"]:
                user_data["updated_at"] = user_data["updated_at"].strftime("%Y-%m-%dT%H:%M")
            users.append({"id": doc.id, **user_data})
        return users
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}

@router.post("")
def create_user(user: UserCreate, current_user: dict = Depends(require_admin)):
    try:
        existing_users = db.collection("users").where(filter=FieldFilter("login", "==", user.login)).stream()
        if any(existing_users):
            raise HTTPException(status_code=400, detail="User with this login already exists")

        hashed_password = hash_password(user.password)

        now = datetime.datetime.utcnow()
        user_data = {
            "login": user.login,
            "password": hashed_password,
            "type": user.type,
            "created_at": now
        }

        doc_ref = db.collection("users").add(user_data)
        response_data = user_data.copy()
        response_data["created_at"] = now.strftime("%Y-%m-%dT%H:%M")
        return {"id": doc_ref[1].id, **response_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}")
def update_user(user_id: str, user: UserUpdate, current_user: dict = Depends(require_admin)):
    try:
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = {}
        if user.login is not None:
            update_data["login"] = user.login
        if user.password is not None:
            update_data["password"] = hash_password(user.password)
        if user.type is not None:
            update_data["type"] = user.type

        if update_data:
            update_data["updated_at"] = datetime.datetime.utcnow()
            doc_ref.update(update_data)

        result = doc_ref.get().to_dict()
        if "created_at" in result and result["created_at"]:
            result["created_at"] = result["created_at"].strftime("%Y-%m-%dT%H:%M")
        if "updated_at" in result and result["updated_at"]:
            result["updated_at"] = result["updated_at"].strftime("%Y-%m-%dT%H:%M")
        return {"id": user_id, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    try:
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found")

        doc_ref.delete()
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


