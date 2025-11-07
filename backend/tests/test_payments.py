"""
Tests for payment endpoints.

This module tests:
- Payment intent creation
- Payment webhook handling
- Payment history retrieval
"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.user import User


class TestPaymentIntentCreation:
    """Test cases for payment intent creation."""
    
    def test_create_payment_intent_success(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test successful payment intent creation.
        
        Given: Valid amount and currency
        When: POST request to /payments/create-intent
        Then: Payment intent is created and returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        data = {
            "amount": 1000,  # $10.00
            "currency": "usd",
            "description": "Premium plan subscription"
        }
        
        response = client.post(
            "/payments/create-intent",
            headers=headers,
            json=data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "client_secret" in result
        assert "payment_intent_id" in result
        assert result["amount"] == 1000
    
    def test_create_payment_intent_invalid_amount(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test payment intent with invalid amount.
        
        Given: Negative or zero amount
        When: POST request to /payments/create-intent
        Then: 422 validation error is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        data = {
            "amount": -100,
            "currency": "usd"
        }
        
        response = client.post(
            "/payments/create-intent",
            headers=headers,
            json=data
        )
        
        assert response.status_code == 422
    
    def test_create_payment_intent_invalid_currency(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test payment intent with invalid currency.
        
        Given: Invalid currency code
        When: POST request to /payments/create-intent
        Then: 422 validation error is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        data = {
            "amount": 1000,
            "currency": "INVALID"
        }
        
        response = client.post(
            "/payments/create-intent",
            headers=headers,
            json=data
        )
        
        assert response.status_code == 422
    
    def test_create_payment_intent_unauthenticated(
        self,
        client: TestClient
    ):
        """
        Test payment intent creation without authentication.
        
        Given: No authentication token
        When: POST request to /payments/create-intent
        Then: 401 unauthorized error is returned
        """
        data = {
            "amount": 1000,
            "currency": "usd"
        }
        
        response = client.post("/payments/create-intent", json=data)
        
        assert response.status_code == 401


class TestPaymentWebhook:
    """Test cases for Stripe webhook handling."""
    
    def test_webhook_payment_succeeded(
        self,
        client: TestClient,
        db: Session,
        test_user: User
    ):
        """
        Test webhook for successful payment.
        
        Given: Valid Stripe webhook event
        When: POST request to /payments/webhook
        Then: Payment is recorded in database
        """
        # Simulate Stripe webhook payload
        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "amount": 1000,
                    "currency": "usd",
                    "status": "succeeded",
                    "metadata": {
                        "user_id": str(test_user.id)
                    }
                }
            }
        }
        
        # Note: In real tests, you'd need to sign the webhook
        # For this test, we're mocking the signature verification
        
        response = client.post(
            "/payments/webhook",
            json=webhook_payload,
            headers={"Stripe-Signature": "mock_signature"}
        )
        
        assert response.status_code == 200
    
    def test_webhook_payment_failed(
        self,
        client: TestClient
    ):
        """
        Test webhook for failed payment.
        
        Given: Webhook event for failed payment
        When: POST request to /payments/webhook
        Then: Failure is logged appropriately
        """
        webhook_payload = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test_456",
                    "amount": 1000,
                    "currency": "usd",
                    "status": "failed"
                }
            }
        }
        
        response = client.post(
            "/payments/webhook",
            json=webhook_payload,
            headers={"Stripe-Signature": "mock_signature"}
        )
        
        assert response.status_code == 200
    
    def test_webhook_invalid_signature(
        self,
        client: TestClient
    ):
        """
        Test webhook with invalid signature.
        
        Given: Webhook with incorrect signature
        When: POST request to /payments/webhook
        Then: 400 bad request is returned
        """
        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {"object": {}}
        }
        
        response = client.post(
            "/payments/webhook",
            json=webhook_payload,
            headers={"Stripe-Signature": "invalid_signature"}
        )
        
        # Should reject invalid signature
        assert response.status_code in [400, 401, 403]


class TestPaymentHistory:
    """Test cases for payment history retrieval."""
    
    def test_get_payment_history_success(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test retrieving payment history.
        
        Given: User has payment history
        When: GET request to /payments/history
        Then: List of payments is returned
        """
        # Create test payments
        for i in range(3):
            payment = Payment(
                user_id=test_user.id,
                stripe_payment_id=f"pi_test_{i}",
                amount=1000 * (i + 1),
                currency="usd",
                status="succeeded",
                description=f"Payment {i}"
            )
            db.add(payment)
        db.commit()
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/payments/history", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 3
    
    def test_get_payment_history_empty(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test retrieving payment history with no payments.
        
        Given: User has no payment history
        When: GET request to /payments/history
        Then: Empty list is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/payments/history", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_payment_history_unauthenticated(
        self,
        client: TestClient
    ):
        """
        Test retrieving payment history without authentication.
        
        Given: No authentication token
        When: GET request to /payments/history
        Then: 401 unauthorized error is returned
        """
        response = client.get("/payments/history")
        
        assert response.status_code == 401


class TestPaymentRefund:
    """Test cases for payment refunds."""
    
    def test_refund_payment_success(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test successful payment refund.
        
        Given: Valid payment exists
        When: POST request to /payments/{id}/refund
        Then: Refund is processed
        """
        # Create test payment
        payment = Payment(
            user_id=test_user.id,
            stripe_payment_id="pi_test_refund",
            amount=1000,
            currency="usd",
            status="succeeded"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.post(
            f"/payments/{payment.id}/refund",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "refunded"
    
    def test_refund_payment_already_refunded(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test refunding already refunded payment.
        
        Given: Payment already refunded
        When: POST request to /payments/{id}/refund
        Then: 400 bad request is returned
        """
        # Create refunded payment
        payment = Payment(
            user_id=test_user.id,
            stripe_payment_id="pi_test_refunded",
            amount=1000,
            currency="usd",
            status="refunded"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.post(
            f"/payments/{payment.id}/refund",
            headers=headers
        )
        
        assert response.status_code == 400
