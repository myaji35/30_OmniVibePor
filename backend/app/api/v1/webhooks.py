"""
Stripe Webhook 핸들러
"""
from fastapi import APIRouter, Request, HTTPException, status
import stripe
from app.core.config import settings
from app.models.user import UserCRUD
from app.services.neo4j_client import get_neo4j_client
from app.models.subscription import PRICING, SubscriptionPlan

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe Webhook 이벤트 처리

    Stripe에서 발생하는 이벤트를 실시간으로 받아서 처리합니다.

    처리하는 이벤트:
    - customer.subscription.created: 구독 생성
    - customer.subscription.updated: 구독 업데이트
    - customer.subscription.deleted: 구독 취소
    - invoice.payment_succeeded: 결제 성공
    - invoice.payment_failed: 결제 실패
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        # Invalid payload
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    # 이벤트 타입별 처리
    event_type = event["type"]
    data_object = event["data"]["object"]

    neo4j_client = get_neo4j_client()
    user_crud = UserCRUD(neo4j_client)

    if event_type == "customer.subscription.created":
        # 구독 생성
        await handle_subscription_created(data_object, user_crud)

    elif event_type == "customer.subscription.updated":
        # 구독 업데이트
        await handle_subscription_updated(data_object, user_crud)

    elif event_type == "customer.subscription.deleted":
        # 구독 취소
        await handle_subscription_deleted(data_object, user_crud)

    elif event_type == "invoice.payment_succeeded":
        # 결제 성공
        await handle_payment_succeeded(data_object, user_crud)

    elif event_type == "invoice.payment_failed":
        # 결제 실패
        await handle_payment_failed(data_object, user_crud)

    return {"status": "success"}


async def handle_subscription_created(subscription: dict, user_crud: UserCRUD):
    """구독 생성 이벤트 처리"""
    customer_id = subscription["customer"]
    subscription_id = subscription["id"]
    status = subscription["status"]

    # Customer의 user_id 조회
    customer = stripe.Customer.retrieve(customer_id)
    user_id = customer.metadata.get("user_id")

    if not user_id:
        return

    # 구독 플랜 확인
    price_id = subscription["items"]["data"][0]["price"]["id"]
    plan = get_plan_from_price_id(price_id)

    if plan:
        plan_details = PRICING[plan]

        # User 정보 업데이트
        user_crud.update_user(user_id, {
            "subscription_tier": plan.value,
            "quota_limit": plan_details["quota_limit"],
            "quota_used": 0,
            "stripe_subscription_id": subscription_id
        })


async def handle_subscription_updated(subscription: dict, user_crud: UserCRUD):
    """구독 업데이트 이벤트 처리"""
    customer_id = subscription["customer"]
    subscription_id = subscription["id"]
    status = subscription["status"]

    # Customer의 user_id 조회
    customer = stripe.Customer.retrieve(customer_id)
    user_id = customer.metadata.get("user_id")

    if not user_id:
        return

    # 구독 플랜 확인
    price_id = subscription["items"]["data"][0]["price"]["id"]
    plan = get_plan_from_price_id(price_id)

    if plan:
        plan_details = PRICING[plan]

        # User 정보 업데이트
        user_crud.update_user(user_id, {
            "subscription_tier": plan.value,
            "quota_limit": plan_details["quota_limit"]
        })


async def handle_subscription_deleted(subscription: dict, user_crud: UserCRUD):
    """구독 취소 이벤트 처리"""
    customer_id = subscription["customer"]

    # Customer의 user_id 조회
    customer = stripe.Customer.retrieve(customer_id)
    user_id = customer.metadata.get("user_id")

    if not user_id:
        return

    # Free 플랜으로 다운그레이드
    user_crud.update_user(user_id, {
        "subscription_tier": "free",
        "quota_limit": 10,
        "quota_used": 0,
        "stripe_subscription_id": None
    })


async def handle_payment_succeeded(invoice: dict, user_crud: UserCRUD):
    """결제 성공 이벤트 처리"""
    customer_id = invoice["customer"]
    subscription_id = invoice["subscription"]

    # Customer의 user_id 조회
    customer = stripe.Customer.retrieve(customer_id)
    user_id = customer.metadata.get("user_id")

    if not user_id:
        return

    # Quota 리셋 (새 결제 기간 시작)
    user_crud.update_user(user_id, {
        "quota_used": 0
    })


async def handle_payment_failed(invoice: dict, user_crud: UserCRUD):
    """결제 실패 이벤트 처리"""
    customer_id = invoice["customer"]

    # Customer의 user_id 조회
    customer = stripe.Customer.retrieve(customer_id)
    user_id = customer.metadata.get("user_id")

    if not user_id:
        return

    # TODO: 사용자에게 이메일 알림 발송
    # TODO: 구독 상태를 "past_due"로 변경


def get_plan_from_price_id(price_id: str) -> SubscriptionPlan:
    """
    Stripe Price ID로 SubscriptionPlan 조회

    Args:
        price_id: Stripe Price ID

    Returns:
        SubscriptionPlan: 구독 플랜
    """
    for plan, details in PRICING.items():
        if details.get("stripe_price_id") == price_id:
            return plan

    return None
