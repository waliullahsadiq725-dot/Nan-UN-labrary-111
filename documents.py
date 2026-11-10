import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..config import settings
from ..database import get_db
from ..models import User, Document, DownloadLog, Bookmark, DocumentReport
from ..dependencies import get_current_user
from ..schemas import ReportIn
from ..utils import document_access_query, serialize_document, remove_document_file

router = APIRouter(prefix="/api", tags=["Documents"])
MAX_BYTES = settings.max_upload_mb * 1024 * 1024

@router.get("/documents")
def list_documents(q: str = Query("", max_length=120),
                   category: str = Query("", max_length=80),
                   department: str = Query("", max_length=120),
                   subject: str = Query("", max_length=120),
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = document_access_query(db, user)
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(or_(Document.title.ilike(term),
                                 Document.description.ilike(term),
                                 Document.original_filename.ilike(term),
                                 Document.subject.ilike(term)))
    if category.strip(): query = query.filter(Document.category == category.strip())
    if department.strip(): query = query.filter(Document.department == department.strip())
    if subject.strip(): query = query.filter(Document.subject == subject.strip())
    docs = query.order_by(Document.created_at.desc()).limit(500).all()
    return [serialize_document(d, user, db) for d in docs]

@router.post("/documents")
async def upload_document(title: str = Form(...), description: str = Form(""),
                          category: str = Form("عمومي"), department: str = Form(""),
                          subject: str = Form(""), visibility: str = Form("university"),
                          file: UploadFile = File(...), db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    if visibility not in ("university", "private"):
        raise HTTPException(400, "د لاسرسي ډول ناسم دی")
    if not title.strip() or len(title) > 200:
        raise HTTPException(400, "د فایل سرلیک اړین دی او تر ۲۰۰ تورو زیات نه وي")
    if Path(file.filename or "").suffix.lower() != ".pdf":
        raise HTTPException(415, "یوازې PDF فایلونه منل کېږي")
    stored_name = f"{uuid.uuid4().hex}.pdf"
    target = settings.upload_path / stored_name
    total = 0
    try:
        with target.open("wb") as output:
            first = await file.read(1024 * 1024)
            total += len(first)
            if not first.startswith(b"%PDF-"):
                raise HTTPException(415, "دا معتبر PDF فایل نه دی")
            output.write(first)
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk: break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise HTTPException(413, f"د فایل اعظمي اندازه {settings.max_upload_mb}MB ده")
                output.write(chunk)
        doc = Document(title=title.strip(), description=description.strip()[:3000],
                       category=category.strip()[:80] or "عمومي",
                       department=department.strip()[:120] or None,
                       subject=subject.strip()[:120] or None, visibility=visibility,
                       original_filename=Path(file.filename).name[:255],
                       stored_filename=stored_name, file_size=total,
                       uploaded_by=user.id, is_approved=(user.role == "admin"))
        db.add(doc); db.commit(); db.refresh(doc)
        return serialize_document(doc, user, db)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

@router.get("/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    doc = document_access_query(db, user).filter(Document.id == document_id).first()
    if not doc: raise HTTPException(404, "فایل ونه موندل شو")
    return serialize_document(doc, user, db)

@router.get("/documents/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    doc = document_access_query(db, user).filter(Document.id == document_id).first()
    if not doc: raise HTTPException(404, "فایل ونه موندل شو یا اجازه نه لرئ")
    path = settings.upload_path / doc.stored_filename
    if not path.is_file(): raise HTTPException(404, "فایل په سرور کې ونه موندل شو")
    doc.downloads += 1
    db.add(DownloadLog(user_id=user.id, document_id=doc.id))
    db.commit()
    return FileResponse(path, media_type="application/pdf", filename=doc.original_filename)

@router.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc: raise HTTPException(404, "فایل ونه موندل شو")
    if user.role != "admin" and doc.uploaded_by != user.id:
        raise HTTPException(403, "یوازې د فایل خاوند یا اډمین یې حذف کولی شي")
    remove_document_file(settings.upload_path, doc.stored_filename)
    db.delete(doc); db.commit()
    return {"message": "فایل حذف شو"}

@router.post("/documents/{document_id}/bookmark")
def toggle_bookmark(document_id: int, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    doc = document_access_query(db, user).filter(Document.id == document_id).first()
    if not doc: raise HTTPException(404, "فایل ونه موندل شو")
    bookmark = db.query(Bookmark).filter_by(user_id=user.id, document_id=document_id).first()
    if bookmark:
        db.delete(bookmark); db.commit()
        return {"bookmarked": False}
    db.add(Bookmark(user_id=user.id, document_id=document_id)); db.commit()
    return {"bookmarked": True}

@router.get("/bookmarks")
def list_bookmarks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Bookmark).filter_by(user_id=user.id).order_by(Bookmark.created_at.desc()).all()
    result = []
    for row in rows:
        doc = document_access_query(db, user).filter(Document.id == row.document_id).first()
        if doc: result.append(serialize_document(doc, user, db))
    return result

@router.post("/documents/{document_id}/report")
def report_document(document_id: int, data: ReportIn,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc: raise HTTPException(404, "فایل ونه موندل شو")
    report = DocumentReport(document_id=document_id, reported_by=user.id, reason=data.reason)
    db.add(report); db.commit()
    return {"message": "راپور ثبت شو"}
