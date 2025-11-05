import datetime
import re
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from config import db
from auth import get_current_user, require_auth, require_admin
from schemas import NoteCreate, NoteUpdate, NoteVisibilityUpdate

router = APIRouter(prefix="/notes", tags=["notes"])

def generate_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug

def find_unique_slug(base_slug: str) -> str:
    existing_docs = db.collection("notes").where("slug", "==", base_slug).stream()
    if not list(existing_docs):
        return base_slug
    
    counter = 2
    while True:
        new_slug = f"{base_slug}-{counter}"
        existing_docs = db.collection("notes").where("slug", "==", new_slug).stream()
        if not list(existing_docs):
            return new_slug
        counter += 1

@router.get("")
def list_notes(current_user: Optional[dict] = Depends(get_current_user)):
    try:
        notes = []
        for doc in db.collection("notes").stream():
            doc_dict = doc.to_dict()
            visible = doc_dict.get("visible", True)
            
            if not visible and (not current_user or current_user["type"] != "admin"):
                continue
            
            created_at = doc_dict.get("created_at")
            updated_at = doc_dict.get("updated_at")
            
            note_data = {
                "id": doc.id,
                "title": doc_dict.get("title"),
                "description": doc_dict.get("description"),
                "tags": doc_dict.get("tags", []),
                "slug": doc_dict.get("slug"),
                "visible": visible,
                "created_at": created_at.strftime("%Y-%m-%dT%H:%M") if created_at else None,
                "updated_at": updated_at.strftime("%Y-%m-%dT%H:%M") if updated_at else None
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
        
        created_at = doc_dict.get("created_at")
        updated_at = doc_dict.get("updated_at")
        
        note_data = {
            "id": doc.id,
            "title": doc_dict.get("title"),
            "description": doc_dict.get("description"),
            "content": doc_dict.get("content"),
            "tags": doc_dict.get("tags", []),
            "terms": doc_dict.get("terms", {}),
            "slug": doc_dict.get("slug"),
            "visible": visible,
            "created_at": created_at.strftime("%Y-%m-%dT%H:%M") if created_at else None,
            "updated_at": updated_at.strftime("%Y-%m-%dT%H:%M") if updated_at else None
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
        
        base_slug = generate_slug(note.title)
        unique_slug = find_unique_slug(base_slug)
        
        now = datetime.datetime.utcnow()
        note_data = {
            "title": note.title,
            "description": note.description,
            "content": note.content,
            "tags": note.tags,
            "terms": note.terms,
            "slug": unique_slug,
            "visible": note.visible,
            "created_at": now,
            "updated_at": now
        }
        doc_ref = db.collection("notes").add(note_data)
        response_data = note_data.copy()
        response_data["created_at"] = now.strftime("%Y-%m-%dT%H:%M")
        response_data["updated_at"] = now.strftime("%Y-%m-%dT%H:%M")
        return {"id": doc_ref[1].id, **response_data}
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

        if current_user["type"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        update_data = {}
        if note.title is not None:
            update_data["title"] = note.title
            base_slug = generate_slug(note.title)
            update_data["slug"] = find_unique_slug(base_slug)
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

        result = doc_ref.get().to_dict()
        if "created_at" in result and result["created_at"]:
            result["created_at"] = result["created_at"].strftime("%Y-%m-%dT%H:%M")
        if "updated_at" in result and result["updated_at"]:
            result["updated_at"] = result["updated_at"].strftime("%Y-%m-%dT%H:%M")
        return {"id": note_id, **result}
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
        update_data["updated_at"] = datetime.datetime.utcnow()
        doc_ref.update(update_data)

        result = doc_ref.get().to_dict()
        if "created_at" in result and result["created_at"]:
            result["created_at"] = result["created_at"].strftime("%Y-%m-%dT%H:%M")
        if "updated_at" in result and result["updated_at"]:
            result["updated_at"] = result["updated_at"].strftime("%Y-%m-%dT%H:%M")
        return {"id": note_id, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
