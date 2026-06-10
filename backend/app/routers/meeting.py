from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import MeetingRoom, MeetingBooking, ApprovalStatus

router = APIRouter(prefix="/api/meeting", tags=["meeting"])


class BookingCreate(BaseModel):
    room_id: int
    booker: str
    title: str
    start_time: datetime
    end_time: datetime
    participants: str = ""


@router.get("/rooms")
def list_rooms(db: Session = Depends(get_db)):
    return db.query(MeetingRoom).all()


@router.get("/bookings")
def list_bookings(db: Session = Depends(get_db)):
    return db.query(MeetingBooking).order_by(MeetingBooking.start_time.desc()).all()


@router.post("/bookings")
def create_booking(req: BookingCreate, db: Session = Depends(get_db)):
    room = db.query(MeetingRoom).filter(MeetingRoom.id == req.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="会议室不存在")

    booking = MeetingBooking(**req.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/bookings/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(MeetingBooking).filter(MeetingBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="预定不存在")
    return booking
