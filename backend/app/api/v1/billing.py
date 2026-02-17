"""
Billing & Subscription API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionPlan,
    PaymentMethod,
    PRICING
)
from app.models.user import UserCRUD
from app.auth.dependencies import get_current_user
from app.services.stripe_service import stripe_service
from app.services.neo4j_client import get_neo4j_client
from app.core.config import settings

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/plans")
async def get_pricing_plans():
    """
    구독 플랜 목록 조회

    Returns:
        list: 모든 구독 플랜 정보
    """
    plans = []
    for plan, details in PRICING.items():
        plans.append({
            "plan": plan.value,
            "name": details["name"],
            "amount": details["amount"],
            "quota_limit": details["quota_limit"],
            "features": details["features"]
        })

    return {"plans": plans}


@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    구독 생성 또는 업그레이드

    Args:
        subscription_data: 구독 생성 정보
        current_user: 현재 사용자

    Returns:
        SubscriptionResponse: 생성된 구독 정보
    """
    user_id = current_user["user_id"]
    email = current_user["email"]
    name = current_user["name"]

    # Stripe Customer 조회 또는 생성
    neo4j_client = get_neo4j_client()
    user_crud = UserCRUD(neo4j_client)

    user = user_crud.get_user_by_id(user_id)
    stripe_customer_id = user.get("stripe_customer_id")

    if not stripe_customer_id:
        # 새 Customer 생성
        stripe_customer_id = await stripe_service.create_customer(
            user_id=user_id,
            email=email,
            name=name
        )

        # User에 stripe_customer_id 저장
        user_crud.update_user(user_id, {"stripe_customer_id": stripe_customer_id})

    # 구독 생성
    stripe_subscription = await stripe_service.create_subscription(
        customer_id=stripe_customer_id,
        plan=subscription_data.plan,
        payment_method_id=subscription_data.payment_method_id
    )

    # User 구독 정보 업데이트
    plan_details = PRICING[subscription_data.plan]
    user_crud.update_user(user_id, {
        "subscription_tier": subscription_data.plan.value,
        "quota_limit": plan_details["quota_limit"],
        "quota_used": 0,
        "stripe_subscription_id": stripe_subscription["id"]
    })

    return SubscriptionResponse(
        subscription_id=stripe_subscription["id"],
        plan=subscription_data.plan,
        status="active",
        quota_limit=plan_details["quota_limit"],
        quota_used=0,
        quota_remaining=plan_details["quota_limit"],
        amount=plan_details["amount"],
        currency="usd",
        current_period_end=stripe_subscription["current_period_end"],
        cancel_at_period_end=False
    )


@router.get("/subscriptions/current", response_model=SubscriptionResponse)
async def get_current_subscription(current_user: dict = Depends(get_current_user)):
    """
    현재 사용자의 구독 정보 조회

    Args:
        current_user: 현재 사용자

    Returns:
        SubscriptionResponse: 구독 정보
    """
    plan = SubscriptionPlan(current_user.get("subscription_tier", "free"))
    quota_limit = current_user.get("quota_limit", 10)
    quota_used = current_user.get("quota_used", 0)

    plan_details = PRICING[plan]

    return SubscriptionResponse(
        subscription_id=current_user.get("stripe_subscription_id", "free"),
        plan=plan,
        status="active",
        quota_limit=quota_limit,
        quota_used=quota_used,
        quota_remaining=max(0, quota_limit - quota_used),
        amount=plan_details["amount"],
        currency="usd",
        current_period_end=current_user.get("subscription_expires_at", ""),
        cancel_at_period_end=False
    )


@router.post("/subscriptions/cancel")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    """
    구독 취소

    현재 기간 종료 시 자동으로 취소됩니다.

    Args:
        current_user: 현재 사용자

    Returns:
        dict: 취소 정보
    """
    stripe_subscription_id = current_user.get("stripe_subscription_id")

    if not stripe_subscription_id or stripe_subscription_id == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription to cancel"
        )

    # Stripe 구독 취소
    await stripe_service.cancel_subscription(stripe_subscription_id)

    return {
        "message": "Subscription will be canceled at the end of the current period",
        "subscription_id": stripe_subscription_id
    }


@router.post("/subscriptions/reactivate")
async def reactivate_subscription(current_user: dict = Depends(get_current_user)):
    """
    취소된 구독 재활성화

    Args:
        current_user: 현재 사용자

    Returns:
        dict: 재활성화 정보
    """
    stripe_subscription_id = current_user.get("stripe_subscription_id")

    if not stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subscription found"
        )

    # Stripe 구독 재활성화
    await stripe_service.reactivate_subscription(stripe_subscription_id)

    return {
        "message": "Subscription reactivated successfully",
        "subscription_id": stripe_subscription_id
    }


@router.post("/checkout")
async def create_checkout_session(
    plan: SubscriptionPlan,
    current_user: dict = Depends(get_current_user)
):
    """
    Stripe Checkout Session 생성

    Args:
        plan: 구독 플랜
        current_user: 현재 사용자

    Returns:
        dict: Checkout URL
    """
    user_id = current_user["user_id"]
    email = current_user["email"]
    name = current_user["name"]

    # Stripe Customer 조회 또는 생성
    neo4j_client = get_neo4j_client()
    user_crud = UserCRUD(neo4j_client)

    user = user_crud.get_user_by_id(user_id)
    stripe_customer_id = user.get("stripe_customer_id")

    if not stripe_customer_id:
        stripe_customer_id = await stripe_service.create_customer(
            user_id=user_id,
            email=email,
            name=name
        )
        user_crud.update_user(user_id, {"stripe_customer_id": stripe_customer_id})

    # Checkout Session 생성
    session = await stripe_service.create_checkout_session(
        customer_id=stripe_customer_id,
        plan=plan,
        success_url=f"{settings.FRONTEND_URL}/billing/success",
        cancel_url=f"{settings.FRONTEND_URL}/billing/cancel"
    )

    return {"checkout_url": session.url}


@router.post("/portal")
async def create_billing_portal(current_user: dict = Depends(get_current_user)):
    """
    Stripe Billing Portal Session 생성

    고객이 구독을 직접 관리할 수 있는 포털

    Args:
        current_user: 현재 사용자

    Returns:
        dict: Billing Portal URL
    """
    stripe_customer_id = current_user.get("stripe_customer_id")

    if not stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer found"
        )

    # Billing Portal Session 생성
    session = await stripe_service.create_billing_portal_session(
        customer_id=stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/billing"
    )

    return {"portal_url": session.url}


@router.get("/invoices")
async def get_invoices(current_user: dict = Depends(get_current_user)):
    """
    청구서 목록 조회

    Args:
        current_user: 현재 사용자

    Returns:
        list: 청구서 목록
    """
    stripe_customer_id = current_user.get("stripe_customer_id")

    if not stripe_customer_id:
        return {"invoices": []}

    # Stripe 청구서 조회
    invoices = await stripe_service.get_invoices(stripe_customer_id)

    return {
        "invoices": [
            {
                "invoice_id": inv.id,
                "amount_due": inv.amount_due / 100,  # cents to dollars
                "amount_paid": inv.amount_paid / 100,
                "status": inv.status,
                "period_start": inv.period_start,
                "period_end": inv.period_end,
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url
            }
            for inv in invoices
        ]
    }


@router.get("/payment-methods", response_model=List[PaymentMethod])
async def get_payment_methods(current_user: dict = Depends(get_current_user)):
    """
    결제 수단 목록 조회

    Args:
        current_user: 현재 사용자

    Returns:
        list: 결제 수단 목록
    """
    stripe_customer_id = current_user.get("stripe_customer_id")

    if not stripe_customer_id:
        return []

    # Stripe 결제 수단 조회
    payment_methods = await stripe_service.get_payment_methods(stripe_customer_id)

    return [
        PaymentMethod(
            payment_method_id=pm.id,
            type=pm.type,
            last4=pm.card.last4,
            brand=pm.card.brand,
            exp_month=pm.card.exp_month,
            exp_year=pm.card.exp_year,
            is_default=False
        )
        for pm in payment_methods
    ]


@router.get("/usage")
async def get_usage_stats(current_user: dict = Depends(get_current_user)):
    """
    사용량 통계 조회

    Args:
        current_user: 현재 사용자

    Returns:
        dict: 사용량 통계
    """
    quota_limit = current_user.get("quota_limit", 10)
    quota_used = current_user.get("quota_used", 0)
    quota_remaining = max(0, quota_limit - quota_used)

    return {
        "quota_limit": quota_limit,
        "quota_used": quota_used,
        "quota_remaining": quota_remaining,
        "usage_percentage": (quota_used / quota_limit * 100) if quota_limit > 0 else 0
    }
