import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from config import db
from auth import get_current_user, require_auth, require_admin
from schemas import NoteCreate, NoteUpdate, NoteVisibilityUpdate

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("")
def list_notes(current_user: Optional[dict] = Depends(get_current_user)):
    try:
        notes = []
        for doc in db.collection("notes").stream():
            doc_dict = doc.to_dict()
            visible = doc_dict.get("visible", True)
            
            if not visible and (not current_user or current_user["type"] != "admin"):
                continue
            
            note_data = {
                "id": doc.id,
                "title": doc_dict.get("title"),
                "description": doc_dict.get("description"),
                "tags": doc_dict.get("tags", []),
                "locked": doc_dict.get("locked", False),
                "visible": visible,
                "created_at": doc_dict.get("created_at"),
                "updated_at": doc_dict.get("updated_at")
            }
            notes.append(note_data)
        return notes
    except Exception as e:
        return {"error": str(e)}

@router.get("/{note_id}")
def get_note(note_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    try:
        doc = db.collection("notes").document(note_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Note not found")
        doc_dict = doc.to_dict()
        
        visible = doc_dict.get("visible", True)
        if not visible and (not current_user or current_user["type"] != "admin"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        note_data = {
            "id": doc.id,
            "title": doc_dict.get("title"),
            "description": doc_dict.get("description"),
            "content": doc_dict.get("content"),
            "tags": doc_dict.get("tags", []),
            "terms": doc_dict.get("terms", {}),
            "locked": doc_dict.get("locked", False),
            "visible": visible,
            "created_at": doc_dict.get("created_at"),
            "updated_at": doc_dict.get("updated_at")
        }
        return note_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def create_note(note: NoteCreate, current_user: dict = Depends(require_auth)):
    try:
        if current_user["type"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        now = datetime.datetime.utcnow()
        note_data = {
            "title": note.title,
            "description": note.description,
            "content": note.content,
            "tags": note.tags,
            "terms": note.terms,
            "locked": False,
            "visible": note.visible,
            "created_at": now,
            "updated_at": now
        }
        doc_ref = db.collection("notes").add(note_data)
        return {"id": doc_ref[1].id, **note_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{note_id}")
def update_note(note_id: str, note: NoteUpdate, current_user: dict = Depends(require_auth)):
    try:
        doc_ref = db.collection("notes").document(note_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Note not found")

        doc_dict = doc.to_dict()
        if doc_dict.get("locked", False) and current_user["type"] != "admin":
            raise HTTPException(status_code=403, detail="Note is locked")

        if current_user["type"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        update_data = {}
        if note.title is not None:
            update_data["title"] = note.title
        if note.description is not None:
            update_data["description"] = note.description
        if note.content is not None:
            update_data["content"] = note.content
        if note.tags is not None:
            update_data["tags"] = note.tags
        if note.terms is not None:
            update_data["terms"] = note.terms

        if update_data:
            update_data["updated_at"] = datetime.datetime.utcnow()
            doc_ref.update(update_data)

        return {"id": note_id, **doc_ref.get().to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{note_id}")
def delete_note(note_id: str, current_user: dict = Depends(require_auth)):
    try:
        doc_ref = db.collection("notes").document(note_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Note not found")

        if current_user["type"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        doc_ref.delete()
        return {"message": "Note deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{note_id}/settings")
def update_note_settings(note_id: str, settings: NoteVisibilityUpdate, current_user: dict = Depends(require_admin)):
    try:
        doc_ref = db.collection("notes").document(note_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Note not found")

        update_data = {"visible": settings.visible}
        if settings.locked is not None:
            update_data["locked"] = settings.locked
        
        update_data["updated_at"] = datetime.datetime.utcnow()
        doc_ref.update(update_data)

        return {"id": note_id, **doc_ref.get().to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
