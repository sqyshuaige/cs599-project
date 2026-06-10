from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Announcement

router = APIRouter(prefix="/api/announcement", tags=["announcement"])


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    publisher: str
    is_pinned: bool = False


@router.get("/")
def list_announcements(db: Session = Depends(get_db)):
    return db.query(Announcement).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()


@router.post("/")
def create_announcement(req: AnnouncementCreate, db: Session = Depends(get_db)):
    announcement = Announcement(**req.model_dump())
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.get("/{announcement_id}")
def get_announcement(announcement_id: int, db: Session = Depends(get_db)):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    return announcement
