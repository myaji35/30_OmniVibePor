"""
Stripe 결제 서비스
"""
from typing import Optional, Dict
from datetime import datetime, timedelta
import stripe
from app.core.config import settings
from app.models.subscription import (
    SubscriptionPlan,
    SubscriptionStatus,
    Subscription,
    PRICING
)

# Stripe API 키 설정
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Stripe 결제 처리 서비스"""

    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_key = self.api_key

    async def create_customer(self, user_id: str, email: str, name: str) -> str:
        """
        Stripe Customer 생성

        Args:
            user_id: 내부 사용자 ID
            email: 사용자 이메일
            name: 사용자 이름

        Returns:
            str: Stripe Customer ID
        """
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"user_id": user_id}
        )

        return customer.id

    async def attach_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> Dict:
        """
        결제 수단을 Customer에 연결

        Args:
            customer_id: Stripe Customer ID
            payment_method_id: Stripe Payment Method ID

        Returns:
            dict: Payment Method 정보
        """
        # Payment Method를 Customer에 연결
        payment_method = stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id
        )

        # 기본 결제 수단으로 설정
        stripe.Customer.modify(
            customer_id,
            invoice_settings={"default_payment_method": payment_method_id}
        )

        return payment_method

    async def create_subscription(
        self,
        customer_id: str,
        plan: SubscriptionPlan,
        payment_method_id: Optional[str] = None
    ) -> Dict:
        """
        구독 생성

        Args:
            customer_id: Stripe Customer ID
            plan: 구독 플랜
            payment_method_id: Stripe Payment Method ID (선택)

        Returns:
            dict: Stripe Subscription 정보
        """
        if plan == SubscriptionPlan.FREE:
            # Free 플랜은 Stripe 구독 없이 처리
            return {
                "id": f"sub_free_{customer_id}",
                "status": "active",
                "current_period_start": int(datetime.utcnow().timestamp()),
                "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp())
            }

        # Payment Method 연결
        if payment_method_id:
            await self.attach_payment_method(customer_id, payment_method_id)

        # Stripe Price ID 가져오기
        price_id = PRICING[plan]["stripe_price_id"]

        # 구독 생성
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"]
        )

        return subscription

    async def cancel_subscription(self, subscription_id: str) -> Dict:
        """
        구독 취소

        Args:
            subscription_id: Stripe Subscription ID

        Returns:
            dict: 취소된 구독 정보
        """
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )

        return subscription

    async def reactivate_subscription(self, subscription_id: str) -> Dict:
        """
        취소된 구독 재활성화

        Args:
            subscription_id: Stripe Subscription ID

        Returns:
            dict: 재활성화된 구독 정보
        """
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False
        )

        return subscription

    async def update_subscription(
        self,
        subscription_id: str,
        new_plan: SubscriptionPlan
    ) -> Dict:
        """
        구독 플랜 변경

        Args:
            subscription_id: Stripe Subscription ID
            new_plan: 새 구독 플랜

        Returns:
            dict: 업데이트된 구독 정보
        """
        # 현재 구독 정보 조회
        subscription = stripe.Subscription.retrieve(subscription_id)

        # 새 Price ID
        new_price_id = PRICING[new_plan]["stripe_price_id"]

        # 구독 항목 업데이트
        subscription = stripe.Subscription.modify(
            subscription_id,
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": new_price_id
            }],
            proration_behavior="create_prorations"
        )

        return subscription

    async def get_customer_subscriptions(self, customer_id: str) -> list:
        """
        Customer의 모든 구독 조회

        Args:
            customer_id: Stripe Customer ID

        Returns:
            list: 구독 목록
        """
        subscriptions = stripe.Subscription.list(customer=customer_id)
        return subscriptions.data

    async def get_invoices(self, customer_id: str, limit: int = 10) -> list:
        """
        Customer의 청구서 목록 조회

        Args:
            customer_id: Stripe Customer ID
            limit: 조회 개수

        Returns:
            list: 청구서 목록
        """
        invoices = stripe.Invoice.list(
            customer=customer_id,
            limit=limit
        )
        return invoices.data

    async def get_payment_methods(self, customer_id: str) -> list:
        """
        Customer의 결제 수단 목록 조회

        Args:
            customer_id: Stripe Customer ID

        Returns:
            list: 결제 수단 목록
        """
        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="card"
        )
        return payment_methods.data

    async def create_checkout_session(
        self,
        customer_id: str,
        plan: SubscriptionPlan,
        success_url: str,
        cancel_url: str
    ) -> Dict:
        """
        Stripe Checkout Session 생성

        Args:
            customer_id: Stripe Customer ID
            plan: 구독 플랜
            success_url: 결제 성공 시 리다이렉트 URL
            cancel_url: 결제 취소 시 리다이렉트 URL

        Returns:
            dict: Checkout Session 정보 (url 포함)
        """
        price_id = PRICING[plan]["stripe_price_id"]

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url
        )

        return session

    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Dict:
        """
        Stripe Billing Portal Session 생성

        고객이 구독을 직접 관리할 수 있는 포털

        Args:
            customer_id: Stripe Customer ID
            return_url: 포털 종료 후 돌아올 URL

        Returns:
            dict: Billing Portal Session 정보 (url 포함)
        """
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )

        return session


# Singleton instance
stripe_service = StripeService()
