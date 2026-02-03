"""감사 로그 서비스"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging
from app.services.neo4j_client import Neo4jClient
from app.core.config import get_settings

settings = get_settings()

# 로거 설정
logger = logging.getLogger("audit")
logger.setLevel(logging.INFO)

# Neo4j 클라이언트
neo4j_client = Neo4jClient()


class AuditEvent:
    """감사 로그 이벤트"""

    def __init__(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.event_id = f"evt_{datetime.utcnow().timestamp()}"
        self.event_type = event_type
        self.user_id = user_id
        self.email = email
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        self.status = status
        self.reason = reason
        self.details = details or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "email": self.email,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
            "details": json.dumps(self.details) if self.details else None,
            "timestamp": self.timestamp.isoformat(),
        }


async def log_auth_event(
    event_type: str,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    인증 이벤트 로깅

    Args:
        event_type: 이벤트 타입 (login_success, login_failed, register_success 등)
        user_id: 사용자 ID
        email: 이메일
        ip_address: IP 주소
        user_agent: User Agent
        status: 상태 (success, failed)
        reason: 실패 사유
        details: 추가 상세 정보
    """
    event = AuditEvent(
        event_type=event_type,
        user_id=user_id,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        reason=reason,
        details=details,
    )

    # 표준 로그 출력
    logger.info(
        f"[AUTH] {event_type} - User: {user_id or email} - Status: {status}"
        + (f" - Reason: {reason}" if reason else "")
    )

    # Neo4j에 저장
    await save_audit_event(event)


async def log_resource_event(
    event_type: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
    status: str = "success",
    reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    리소스 접근/변경 이벤트 로깅

    Args:
        event_type: 이벤트 타입
        user_id: 사용자 ID
        resource_type: 리소스 타입 (project, audio, video 등)
        resource_id: 리소스 ID
        action: 액션 (create, update, delete, view 등)
        status: 상태 (success, failed)
        reason: 실패 사유
        details: 추가 상세 정보
    """
    event = AuditEvent(
        event_type=event_type,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        status=status,
        reason=reason,
        details=details,
    )

    # 표준 로그 출력
    logger.info(
        f"[RESOURCE] {action} {resource_type}:{resource_id} - User: {user_id} - Status: {status}"
        + (f" - Reason: {reason}" if reason else "")
    )

    # Neo4j에 저장
    await save_audit_event(event)


async def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    reason: str = "",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    보안 이벤트 로깅

    Args:
        event_type: 이벤트 타입 (rate_limit_exceeded, invalid_token 등)
        user_id: 사용자 ID
        ip_address: IP 주소
        reason: 사유
        details: 추가 상세 정보
    """
    event = AuditEvent(
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        status="failed",
        reason=reason,
        details=details,
    )

    # 표준 로그 출력
    logger.warning(
        f"[SECURITY] {event_type} - User: {user_id or 'Anonymous'} - IP: {ip_address} - {reason}"
    )

    # Neo4j에 저장
    await save_audit_event(event)


async def save_audit_event(event: AuditEvent) -> bool:
    """
    감사 로그를 Neo4j에 저장

    Args:
        event: 감사 이벤트

    Returns:
        저장 성공 여부
    """
    try:
        query = """
        CREATE (e:AuditEvent {
            event_id: $event_id,
            event_type: $event_type,
            user_id: $user_id,
            email: $email,
            ip_address: $ip_address,
            user_agent: $user_agent,
            resource_type: $resource_type,
            resource_id: $resource_id,
            action: $action,
            status: $status,
            reason: $reason,
            details: $details,
            timestamp: datetime($timestamp)
        })
        """

        # 사용자와 연결
        if event.user_id:
            query += """
            WITH e
            MATCH (u:User {user_id: $user_id})
            CREATE (u)-[:PERFORMED]->(e)
            """

        query += "RETURN e.event_id as event_id"

        result = neo4j_client.query(query, event.to_dict())
        return len(result) > 0

    except Exception as e:
        logger.error(f"Failed to save audit event: {e}")
        return False


async def get_user_audit_logs(
    user_id: str,
    event_type: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
) -> List[Dict[str, Any]]:
    """
    사용자의 감사 로그 조회

    Args:
        user_id: 사용자 ID
        event_type: 이벤트 타입 필터
        limit: 최대 레코드 수
        skip: 건너뛸 레코드 수

    Returns:
        감사 로그 목록
    """
    where_clause = ""
    if event_type:
        where_clause = "AND e.event_type = $event_type"

    query = f"""
    MATCH (u:User {{user_id: $user_id}})-[:PERFORMED]->(e:AuditEvent)
    WHERE 1=1 {where_clause}
    RETURN e.event_id as event_id,
           e.event_type as event_type,
           e.resource_type as resource_type,
           e.resource_id as resource_id,
           e.action as action,
           e.status as status,
           e.reason as reason,
           e.details as details,
           e.timestamp as timestamp
    ORDER BY e.timestamp DESC
    SKIP $skip
    LIMIT $limit
    """

    params = {"user_id": user_id, "skip": skip, "limit": limit}
    if event_type:
        params["event_type"] = event_type

    results = neo4j_client.query(query, params)

    # Neo4j DateTime을 Python datetime으로 변환
    for row in results:
        if row.get("timestamp"):
            row["timestamp"] = row["timestamp"].to_native()
        if row.get("details"):
            try:
                row["details"] = json.loads(row["details"])
            except json.JSONDecodeError:
                pass

    return results


async def get_security_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    보안 이벤트 조회 (관리자용)

    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        event_type: 이벤트 타입 필터
        limit: 최대 레코드 수

    Returns:
        보안 이벤트 목록
    """
    where_clauses = ["e.status = 'failed'"]

    if start_date:
        where_clauses.append("e.timestamp >= datetime($start_date)")

    if end_date:
        where_clauses.append("e.timestamp <= datetime($end_date)")

    if event_type:
        where_clauses.append("e.event_type = $event_type")

    where_clause = " AND ".join(where_clauses)

    query = f"""
    MATCH (e:AuditEvent)
    WHERE {where_clause}
    RETURN e.event_id as event_id,
           e.event_type as event_type,
           e.user_id as user_id,
           e.email as email,
           e.ip_address as ip_address,
           e.user_agent as user_agent,
           e.reason as reason,
           e.details as details,
           e.timestamp as timestamp
    ORDER BY e.timestamp DESC
    LIMIT $limit
    """

    params = {"limit": limit}
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()
    if event_type:
        params["event_type"] = event_type

    results = neo4j_client.query(query, params)

    # Neo4j DateTime을 Python datetime으로 변환
    for row in results:
        if row.get("timestamp"):
            row["timestamp"] = row["timestamp"].to_native()
        if row.get("details"):
            try:
                row["details"] = json.loads(row["details"])
            except json.JSONDecodeError:
                pass

    return results


async def get_audit_statistics(
    user_id: Optional[str] = None,
    days: int = 30,
) -> Dict[str, Any]:
    """
    감사 로그 통계

    Args:
        user_id: 사용자 ID (전체 통계의 경우 None)
        days: 통계 기간 (일)

    Returns:
        통계 데이터
    """
    user_filter = ""
    if user_id:
        user_filter = "MATCH (u:User {user_id: $user_id})-[:PERFORMED]->(e)"
    else:
        user_filter = "MATCH (e:AuditEvent)"

    query = f"""
    {user_filter}
    WHERE datetime() - e.timestamp <= duration({{days: $days}})
    WITH e.event_type as event_type, e.status as status, count(*) as count
    RETURN event_type, status, count
    """

    params = {"days": days}
    if user_id:
        params["user_id"] = user_id

    results = neo4j_client.query(query, params)

    # 통계 집계
    stats = {
        "total_events": 0,
        "success_events": 0,
        "failed_events": 0,
        "by_type": {},
    }

    for row in results:
        event_type = row["event_type"]
        status = row["status"]
        count = row["count"]

        stats["total_events"] += count

        if status == "success":
            stats["success_events"] += count
        else:
            stats["failed_events"] += count

        if event_type not in stats["by_type"]:
            stats["by_type"][event_type] = {"success": 0, "failed": 0}

        stats["by_type"][event_type][status] += count

    return stats
