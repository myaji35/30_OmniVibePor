"""
Quota 관리 Celery Tasks
"""
from celery import Task
from app.tasks.celery_app import celery_app
from app.services.neo4j_client import get_neo4j_client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="quota.reset_monthly_quotas")
def reset_monthly_quotas():
    """
    모든 사용자의 월별 Quota 리셋

    매월 1일 00:00에 실행됩니다. (Celery Beat로 스케줄링)
    """
    try:
        neo4j_client = get_neo4j_client()

        # 모든 사용자의 quota_used를 0으로 리셋
        query = """
        MATCH (u:User)
        WHERE u.is_active = true
        SET u.quota_used = 0,
            u.updated_at = datetime()
        RETURN count(u) as reset_count
        """

        result = neo4j_client.query(query)
        reset_count = result[0]["reset_count"] if result else 0

        logger.info(f"✅ Monthly quota reset completed: {reset_count} users")

        return {
            "status": "success",
            "reset_count": reset_count,
            "reset_date": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Monthly quota reset failed: {str(e)}")
        raise


@celery_app.task(name="quota.check_quota_warnings")
def check_quota_warnings():
    """
    Quota 80% 이상 사용자에게 경고 알림

    매일 실행됩니다.
    """
    try:
        neo4j_client = get_neo4j_client()

        # Quota 80% 이상 사용자 조회
        query = """
        MATCH (u:User)
        WHERE u.is_active = true
          AND u.quota_used >= u.quota_limit * 0.8
          AND u.quota_used < u.quota_limit
        RETURN u.user_id as user_id,
               u.email as email,
               u.name as name,
               u.quota_limit as quota_limit,
               u.quota_used as quota_used
        """

        users = neo4j_client.query(query)

        warning_count = 0
        for user in users:
            # TODO: 이메일 알림 발송
            logger.info(
                f"⚠️ Quota warning: {user['email']} "
                f"({user['quota_used']}/{user['quota_limit']})"
            )
            warning_count += 1

        logger.info(f"✅ Quota warnings checked: {warning_count} users notified")

        return {
            "status": "success",
            "warning_count": warning_count
        }

    except Exception as e:
        logger.error(f"❌ Quota warning check failed: {str(e)}")
        raise


@celery_app.task(name="quota.generate_usage_report")
def generate_usage_report():
    """
    월별 사용량 리포트 생성

    매월 말일에 실행됩니다.
    """
    try:
        neo4j_client = get_neo4j_client()

        # 전체 사용량 통계
        query = """
        MATCH (u:User)
        WHERE u.is_active = true
        RETURN u.subscription_tier as plan,
               count(u) as user_count,
               sum(u.quota_used) as total_used,
               avg(u.quota_used) as avg_used,
               max(u.quota_used) as max_used
        """

        stats = neo4j_client.query(query)

        logger.info("📊 Monthly usage report generated")
        for stat in stats:
            logger.info(
                f"  {stat['plan']}: "
                f"{stat['user_count']} users, "
                f"{stat['total_used']} total, "
                f"{stat['avg_used']:.2f} avg"
            )

        return {
            "status": "success",
            "report": stats,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Usage report generation failed: {str(e)}")
        raise
