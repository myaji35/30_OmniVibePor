"""
Subscription & Billing Models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class SubscriptionPlan(str, Enum):
    """구독 플랜"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """구독 상태"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class Subscription(BaseModel):
    """구독 정보"""
    subscription_id: str
    user_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus

    # Stripe 정보
    stripe_customer_id: str
    stripe_subscription_id: Optional[str] = None
    stripe_payment_method_id: Optional[str] = None

    # Quota
    quota_limit: int  # 월별 영상 생성 제한
    quota_used: int = 0
    quota_reset_at: datetime

    # 금액
    amount: float  # USD
    currency: str = "usd"

    # 기간
    current_period_start: datetime
    current_period_end: datetime

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    canceled_at: Optional[datetime] = None


class SubscriptionCreate(BaseModel):
    """구독 생성 요청"""
    plan: SubscriptionPlan
    payment_method_id: str  # Stripe Payment Method ID


class SubscriptionResponse(BaseModel):
    """구독 응답"""
    subscription_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    quota_limit: int
    quota_used: int
    quota_remaining: int
    amount: float
    currency: str
    current_period_end: datetime
    cancel_at_period_end: bool


class PaymentMethod(BaseModel):
    """결제 수단"""
    payment_method_id: str
    type: str  # card, bank_account
    last4: str
    brand: Optional[str] = None  # visa, mastercard, etc
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool = False


class Invoice(BaseModel):
    """청구서"""
    invoice_id: str
    subscription_id: str
    user_id: str

    amount_due: float
    amount_paid: float
    currency: str = "usd"

    status: str  # paid, open, void, uncollectible

    # 기간
    period_start: datetime
    period_end: datetime

    # Stripe
    stripe_invoice_id: str
    hosted_invoice_url: Optional[str] = None
    invoice_pdf: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class UsageRecord(BaseModel):
    """사용량 기록"""
    usage_id: str
    user_id: str
    subscription_id: str

    # 사용량
    videos_created: int
    audio_generated_minutes: int
    storage_used_gb: float

    # 기간
    period_start: datetime
    period_end: datetime

    created_at: datetime = Field(default_factory=datetime.utcnow)


# Pricing Configuration
PRICING = {
    SubscriptionPlan.FREE: {
        "amount": 0,
        "quota_limit": 10,
        "name": "Free",
        "features": [
            "10 videos per month",
            "Basic templates",
            "Community support"
        ]
    },
    SubscriptionPlan.PRO: {
        "amount": 49,
        "quota_limit": 100,
        "stripe_price_id": "price_pro_monthly",  # Stripe에서 생성한 Price ID
        "name": "Pro",
        "features": [
            "100 videos per month",
            "All templates",
            "Voice cloning",
            "Priority support"
        ]
    },
    SubscriptionPlan.ENTERPRISE: {
        "amount": 499,
        "quota_limit": 9999,  # Unlimited
        "stripe_price_id": "price_enterprise_monthly",
        "name": "Enterprise",
        "features": [
            "Unlimited videos",
            "Custom templates",
            "Dedicated support",
            "API access",
            "White-label"
        ]
    }
}
