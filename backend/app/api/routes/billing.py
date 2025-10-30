"""
Billing and Subscription API Routes

Handles Stripe integration for subscription management
"""

import os
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
import stripe

from app.core.database import get_collection
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class CheckoutRequest(BaseModel):
    plan: str  # "pro" or "enterprise"


@router.get("/subscription")
async def get_subscription(request: Request):
    """
    Get current subscription details.

    Returns subscription status, plan, and payment method.
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        users_collection = get_collection("users")
        user_doc = await users_collection.find_one({"uid": uid})

        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        subscription_data = {
            "plan": user_doc.get("plan", "free"),
            "subscription_status": user_doc.get("subscription_status", "active"),
            "stripe_customer_id": user_doc.get("stripe_customer_id"),
            "stripe_subscription_id": user_doc.get("stripe_subscription_id"),
        }

        # If has Stripe subscription, fetch details
        if user_doc.get("stripe_subscription_id"):
            try:
                subscription = stripe.Subscription.retrieve(user_doc["stripe_subscription_id"])
                subscription_data["current_period_end"] = subscription.current_period_end
                subscription_data["cancel_at_period_end"] = subscription.cancel_at_period_end

                # Get payment method
                if subscription.default_payment_method:
                    pm_id = str(subscription.default_payment_method)
                    payment_method = stripe.PaymentMethod.retrieve(pm_id)
                    if payment_method.card:
                        subscription_data["payment_method"] = {
                            "brand": payment_method.card.brand if hasattr(payment_method.card, 'brand') else 'unknown',
                            "last4": payment_method.card.last4 if hasattr(payment_method.card, 'last4') else '****',
                            "exp_month": payment_method.card.exp_month if hasattr(payment_method.card, 'exp_month') else 0,
                            "exp_year": payment_method.card.exp_year if hasattr(payment_method.card, 'exp_year') else 0,
                        }
            except Exception as stripe_error:
                logger.error(f"Stripe API error: {str(stripe_error)}")

        return {"data": subscription_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription")


@router.post("/create-checkout")
async def create_checkout_session(request: Request, checkout_request: CheckoutRequest):
    """
    Create Stripe Checkout session for subscription upgrade.

    Returns checkout URL to redirect user.
    """
    user = get_current_user(request)
    uid = user["uid"]
    email = user["email"]

    try:
        users_collection = get_collection("users")
        user_doc = await users_collection.find_one({"uid": uid})

        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if already subscribed
        if user_doc.get("plan") == "pro" and user_doc.get("subscription_status") == "active":
            raise HTTPException(status_code=400, detail="Already subscribed to Pro plan")

        # Get or create Stripe customer
        customer_id = user_doc.get("stripe_customer_id")

        if not customer_id:
            customer = stripe.Customer.create(
                email=email,
                metadata={"firebase_uid": uid}
            )
            customer_id = customer.id

            # Save customer ID
            await users_collection.update_one(
                {"uid": uid},
                {"$set": {"stripe_customer_id": customer_id}}
            )

        # Define price (would be environment variable in production)
        price_id = os.getenv("STRIPE_PRO_PRICE_ID", "price_pro_monthly")

        # Create Checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=os.getenv("FRONTEND_URL", "http://localhost:5173") + "/billing?success=true",
            cancel_url=os.getenv("FRONTEND_URL", "http://localhost:5173") + "/billing?canceled=true",
            metadata={"firebase_uid": uid}
        )

        return {
            "data": {"checkout_url": checkout_session.url},
            "message": "Redirect to checkout URL"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/cancel-subscription")
async def cancel_subscription(request: Request):
    """
    Cancel current subscription (effective at period end).
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        users_collection = get_collection("users")
        user_doc = await users_collection.find_one({"uid": uid})

        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        subscription_id = user_doc.get("stripe_subscription_id")

        if not subscription_id:
            raise HTTPException(status_code=400, detail="No active subscription")

        # Cancel subscription at period end
        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )

        return {"message": "Subscription will cancel at end of billing period"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/usage")
async def get_usage(request: Request):
    """
    Get current billing cycle usage.
    """
    user = get_current_user(request)
    uid = user["uid"]

    try:
        users_collection = get_collection("users")
        user_doc = await users_collection.find_one({"uid": uid})

        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        api_calls_used = user_doc.get("api_calls_used", 0)
        api_calls_limit = user_doc.get("api_calls_limit", 100)
        scan_credits_used = user_doc.get("scan_credits_used", 0)
        scan_credits_limit = user_doc.get("scan_credits_limit", 10)

        return {
            "data": {
                "api_calls_used": api_calls_used,
                "api_calls_limit": api_calls_limit,
                "api_calls_percentage": (api_calls_used / api_calls_limit * 100) if api_calls_limit > 0 else 0,
                "scan_credits_used": scan_credits_used,
                "scan_credits_limit": scan_credits_limit,
                "scan_credits_percentage": (scan_credits_used / scan_credits_limit * 100) if scan_credits_limit > 0 else 0,
                "usage_reset_at": user_doc.get("usage_reset_at", "").isoformat() if user_doc.get("usage_reset_at") else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get usage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage")


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Handle Stripe webhook events.
    
    Processes subscription lifecycle events:
    - subscription.created
    - subscription.updated
    - subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    try:
        # Get webhook secret
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            logger.error("Stripe webhook secret not configured")
            raise HTTPException(status_code=500, detail="Webhook not configured")
        
        # Get raw body
        payload = await request.body()
        
        # Verify signature
        try:
            event = stripe.Webhook.construct_event(  # type: ignore
                payload, stripe_signature, webhook_secret
            )
        except Exception:  # type: ignore
            logger.error("Invalid Stripe signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle event
        event_type = event["type"]
        data = event["data"]["object"]
        
        users_collection = get_collection("users")
        
        if event_type == "checkout.session.completed":
            # Payment successful - activate subscription
            customer_id = data["customer"]
            subscription_id = data["subscription"]
            
            # Get user by customer ID
            user_doc = await users_collection.find_one({"stripe_customer_id": customer_id})
            if user_doc:
                # Update user subscription
                await users_collection.update_one(
                    {"uid": user_doc["uid"]},
                    {
                        "$set": {
                            "plan": "pro",
                            "subscription_status": "active",
                            "stripe_subscription_id": subscription_id,
                            "scan_credits_limit": 999999,  # Unlimited for Pro
                            "api_calls_limit": 999999,     # Unlimited for Pro
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Activated Pro subscription for user {user_doc['uid']}")
        
        elif event_type == "customer.subscription.updated":
            # Subscription updated
            subscription_id = data["id"]
            status = data["status"]
            
            user_doc = await users_collection.find_one({"stripe_subscription_id": subscription_id})
            if user_doc:
                await users_collection.update_one(
                    {"uid": user_doc["uid"]},
                    {
                        "$set": {
                            "subscription_status": status,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Updated subscription status to {status} for user {user_doc['uid']}")
        
        elif event_type == "customer.subscription.deleted":
            # Subscription cancelled
            subscription_id = data["id"]
            
            user_doc = await users_collection.find_one({"stripe_subscription_id": subscription_id})
            if user_doc:
                # Downgrade to free plan
                await users_collection.update_one(
                    {"uid": user_doc["uid"]},
                    {
                        "$set": {
                            "plan": "free",
                            "subscription_status": "cancelled",
                            "stripe_subscription_id": None,
                            "scan_credits_limit": 10,
                            "api_calls_limit": 100,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Downgraded user {user_doc['uid']} to free plan")
        
        elif event_type == "invoice.payment_succeeded":
            # Payment succeeded - reset usage
            subscription_id = data["subscription"]
            
            user_doc = await users_collection.find_one({"stripe_subscription_id": subscription_id})
            if user_doc:
                # Reset monthly usage
                next_reset = datetime.utcnow() + timedelta(days=30)
                await users_collection.update_one(
                    {"uid": user_doc["uid"]},
                    {
                        "$set": {
                            "scan_credits_used": 0,
                            "api_calls_used": 0,
                            "usage_reset_at": next_reset,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Reset usage for user {user_doc['uid']}")
        
        elif event_type == "invoice.payment_failed":
            # Payment failed
            subscription_id = data["subscription"]
            
            user_doc = await users_collection.find_one({"stripe_subscription_id": subscription_id})
            if user_doc:
                await users_collection.update_one(
                    {"uid": user_doc["uid"]},
                    {
                        "$set": {
                            "subscription_status": "past_due",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.warning(f"Payment failed for user {user_doc['uid']}")
        
        return {"status": "success"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
