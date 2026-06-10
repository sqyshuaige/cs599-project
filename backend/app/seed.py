from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import (
    LeaveRequest, LeaveType, ExpenseReport, ApprovalStatus,
    Announcement, MeetingRoom, MeetingBooking
)


def seed_data():
    db = SessionLocal()
    try:
        existing = db.query(MeetingRoom).count()
        if existing > 0:
            return

        rooms = [
            MeetingRoom(name="创新厅", capacity=20, location="1楼101室", equipment="投影仪、视频会议系统"),
            MeetingRoom(name="协作厅", capacity=10, location="1楼102室", equipment="白板、电视"),
            MeetingRoom(name="专注厅", capacity=6, location="1楼103室", equipment="白板"),
            MeetingRoom(name="远见厅", capacity=30, location="2楼201室", equipment="投影仪、视频会议系统、音响"),
            MeetingRoom(name="灵感厅", capacity=4, location="2楼202室", equipment=""),
        ]
        db.add_all(rooms)

        announcements = [
            Announcement(
                title="关于2025年端午节放假安排的通知",
                content="根据国家法定节假日安排，2025年端午节放假时间为6月10日（星期二）至6月12日（星期四），共3天。6月13日（星期五）正常上班。请各部门提前做好工作安排。",
                publisher="人力资源部",
                is_pinned=True,
            ),
            Announcement(
                title="OA系统AI助手功能上线通知",
                content="为提升办公效率，公司OA系统正式上线AI智能助手功能。员工可通过AI助手查询政策、创建申请、查询状态等。欢迎大家体验并提出宝贵意见。",
                publisher="技术研发部",
                is_pinned=True,
            ),
            Announcement(
                title="季度绩效考核通知",
                content="2025年第二季度绩效考核将于6月15日开始，请各部门经理于6月30日前完成员工绩效评估。评估标准详见附件。",
                publisher="人力资源部",
                is_pinned=False,
            ),
        ]
        db.add_all(announcements)

        now = datetime.now()
        leaves = [
            LeaveRequest(
                applicant="张三",
                department="技术研发部",
                leave_type=LeaveType.ANNUAL,
                start_date=now + timedelta(days=5),
                end_date=now + timedelta(days=7),
                reason="回老家探亲",
                status=ApprovalStatus.PENDING,
            ),
            LeaveRequest(
                applicant="李四",
                department="产品设计部",
                leave_type=LeaveType.SICK,
                start_date=now - timedelta(days=2),
                end_date=now + timedelta(days=1),
                reason="感冒发烧，需休息",
                status=ApprovalStatus.APPROVED,
                approver="王经理",
                approval_comment="好好休息，早日康复",
            ),
            LeaveRequest(
                applicant="王五",
                department="市场运营部",
                leave_type=LeaveType.PERSONAL,
                start_date=now + timedelta(days=10),
                end_date=now + timedelta(days=11),
                reason="家中急事需处理",
                status=ApprovalStatus.PENDING,
            ),
        ]
        db.add_all(leaves)

        expenses = [
            ExpenseReport(
                applicant="张三",
                department="技术研发部",
                category="差旅费",
                amount=3200.00,
                description="赴上海参加AI技术峰会，含往返高铁票560元、住宿3晚1050元、餐饮补贴300元、会议注册费1290元",
                status=ApprovalStatus.PENDING,
            ),
            ExpenseReport(
                applicant="李四",
                department="产品设计部",
                category="办公用品",
                amount=450.00,
                description="采购设计用笔记本和马克笔套装",
                status=ApprovalStatus.APPROVED,
                approver="王经理",
                approval_comment="合理支出，已批准",
            ),
            ExpenseReport(
                applicant="赵六",
                department="市场运营部",
                category="业务招待费",
                amount=1800.00,
                description="接待重要客户晚宴",
                status=ApprovalStatus.PENDING,
            ),
            ExpenseReport(
                applicant="张三",
                department="技术研发部",
                category="差旅费",
                amount=8500.00,
                description="赴深圳参加开发者大会，含机票4500元、住宿4晚2000元、餐饮补贴500元、交通500元、会议注册费1000元",
                status=ApprovalStatus.PENDING,
            ),
        ]
        db.add_all(expenses)

        bookings = [
            MeetingBooking(
                room_id=1,
                booker="张三",
                title="AI项目周会",
                start_time=now + timedelta(days=1, hours=8),
                end_time=now + timedelta(days=1, hours=8, minutes=30),
                participants="张三,李四,王五,赵六",
            ),
            MeetingBooking(
                room_id=4,
                booker="王经理",
                title="季度总结会",
                start_time=now + timedelta(days=3, hours=6),
                end_time=now + timedelta(days=3, hours=8),
                participants="各部门经理",
            ),
        ]
        db.add_all(bookings)

        db.commit()
        print("✅ 测试数据初始化完成")
    finally:
        db.close()
