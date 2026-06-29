"""
邀请码业务逻辑模块
"""
import secrets
import string

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.invitation import InvitationRecord
from app.utils.logger import app_logger


# 邀请码字符集（排除易混淆字符：0, O, 1, I, L）
INVITE_CODE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
# 邀请码长度
INVITE_CODE_LENGTH = 6
# 每个用户最多填写邀请码次数
MAX_USE_INVITE_COUNT = 5
# 每个邀请码最多奖励次数
MAX_INVITE_REWARD_COUNT = 5
# 每次邀请奖励积分
INVITE_REWARD_POINTS = 50


def generate_invite_code(db: Session) -> str:
    """
    生成唯一的邀请码

    Args:
        db: 数据库Session

    Returns:
        6位邀请码字符串
    """
    while True:
        # 生成6位随机邀请码
        code = ''.join(secrets.choice(INVITE_CODE_CHARS) for _ in range(INVITE_CODE_LENGTH))

        # 检查是否已存在
        existing = db.query(User).filter(User.invite_code == code).first()
        if not existing:
            return code


def get_invitation_stats(db: Session, user_id: int) -> dict:
    """
    获取用户邀请统计信息

    Args:
        db: 数据库Session
        user_id: 用户ID

    Returns:
        包含邀请统计的字典
    """
    # 从 users 表读取计数字段（已在事务中保证一致性）
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {
            "invite_reward_count": 0,
            "invite_reward_remaining": MAX_INVITE_REWARD_COUNT,
            "used_invite_count": 0,
            "used_invite_remaining": MAX_USE_INVITE_COUNT
        }

    invite_reward_count = user.invite_reward_count or 0
    used_invite_count = user.used_invite_count or 0

    return {
        "invite_reward_count": invite_reward_count,
        "invite_reward_remaining": MAX_INVITE_REWARD_COUNT - invite_reward_count,
        "used_invite_count": used_invite_count,
        "used_invite_remaining": MAX_USE_INVITE_COUNT - used_invite_count
    }


def use_invite_code(
    db: Session,
    invitee_user_id: int,
    invite_code: str,
    auto_commit: bool = True
) -> InvitationRecord:
    """
    使用邀请码

    Args:
        db: 数据库Session
        invitee_user_id: 填写邀请码的用户ID
        invite_code: 邀请码
        auto_commit: 是否自动提交事务，默认True

    Returns:
        邀请记录对象

    Raises:
        HTTPException: 各种校验失败时抛出异常
    """
    # 标准化邀请码：去掉首尾空格并转大写
    invite_code = invite_code.strip().upper()

    # 查询邀请码对应的邀请人
    inviter_user = db.query(User).filter(User.invite_code == invite_code).first()
    if not inviter_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码不存在"
        )

    # 邀请人是当前用户则报错
    if inviter_user.id == invitee_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能填写自己的邀请码"
        )

    # 按用户ID从小到大排序加锁，避免死锁
    user_ids = sorted([inviter_user.id, invitee_user_id])
    locked_users = {}
    for uid in user_ids:
        # populate_existing=True 强制从数据库重新加载，避免 identity map 复用旧对象
        user = db.query(User).filter(User.id == uid).with_for_update().populate_existing().first()
        locked_users[uid] = user

    # 从锁住的用户行直接读取计数字段（避免 REPEATABLE READ 快照问题）
    invitee_user = locked_users[invitee_user_id]
    locked_inviter_user = locked_users[inviter_user.id]

    # 检查当前用户已填写邀请码次数
    if (invitee_user.used_invite_count or 0) >= MAX_USE_INVITE_COUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="你已达到邀请码填写次数上限"
        )

    # 检查该邀请码已产生奖励次数
    if (locked_inviter_user.invite_reward_count or 0) >= MAX_INVITE_REWARD_COUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邀请码奖励次数已用完"
        )

    # 检查当前用户是否已填写过该邀请人的邀请码
    existing_record = db.query(InvitationRecord).filter(
        InvitationRecord.invitee_user_id == invitee_user_id,
        InvitationRecord.inviter_user_id == inviter_user.id
    ).with_for_update().first()

    if existing_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="你已经填写过该用户的邀请码"
        )

    # 创建邀请记录
    invitation_record = InvitationRecord(
        inviter_user_id=inviter_user.id,
        invitee_user_id=invitee_user_id,
        invite_code=invite_code,
        reward_points=INVITE_REWARD_POINTS,
        reward_granted=1
    )
    db.add(invitation_record)
    db.flush()

    # 递增用户计数字段（在锁内操作，保证并发安全）
    locked_inviter_user.invite_reward_count = (locked_inviter_user.invite_reward_count or 0) + 1
    invitee_user.used_invite_count = (invitee_user.used_invite_count or 0) + 1

    # 调用 point_service 给邀请人加积分（延迟导入避免循环依赖）
    from app.services.point_service import add_points
    add_points(
        db=db,
        user_id=inviter_user.id,
        points=INVITE_REWARD_POINTS,
        transaction_type="invite_reward",
        related_order_no=f"INVITE_{invitation_record.id}",
        remark="邀请用户使用邀请码奖励",
        auto_commit=False,
        count_as_recharge=False
    )

    # 给填写人加积分
    add_points(
        db=db,
        user_id=invitee_user_id,
        points=INVITE_REWARD_POINTS,
        transaction_type="invite_reward",
        related_order_no=f"INVITE_{invitation_record.id}",
        remark="填写邀请码奖励",
        auto_commit=False,
        count_as_recharge=False
    )

    if auto_commit:
        db.commit()

    app_logger.info(
        f"邀请码使用成功: inviter={inviter_user.id}, invitee={invitee_user_id}, "
        f"invite_code={invite_code}, reward_points={INVITE_REWARD_POINTS}"
    )

    return invitation_record
