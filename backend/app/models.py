import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, Boolean
from app.database import Base


class LeaveType(str, enum.Enum):
    ANNUAL = "年假"
    SICK = "病假"
    PERSONAL = "事假"
    MARRIAGE = "婚假"
    MATERNITY = "产假"


class ApprovalStatus(str, enum.Enum):
    PENDING = "待审批"
    APPROVED = "已通过"
    REJECTED = "已驳回"


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant = Column(String(50), nullable=False)
    department = Column(String(50), nullable=False)
    leave_type = Column(Enum(LeaveType), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approver = Column(String(50), default="")
    approval_comment = Column(Text, default="")
    agent_suggestion = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)


class ExpenseReport(Base):
    __tablename__ = "expense_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant = Column(String(50), nullable=False)
    department = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approver = Column(String(50), default="")
    approval_comment = Column(Text, default="")
    anomaly_flag = Column(Boolean, default=False)
    anomaly_reason = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    publisher = Column(String(50), nullable=False)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class MeetingRoom(Base):
    __tablename__ = "meeting_rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(String(100), nullable=False)
    equipment = Column(String(200), default="")
    is_available = Column(Boolean, default=True)


class MeetingBooking(Base):
    __tablename__ = "meeting_bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, nullable=False)
    booker = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    participants = Column(Text, default="")
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    created_at = Column(DateTime, default=datetime.now)
