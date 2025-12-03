from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
from pywebpush import webpush, WebPushException

from ..database import get_db
from ..models import User, PushSubscription
from ..auth import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses={404: {"description": "Not found"}},
)

# VAPID Keys (Generated via npx web-push generate-vapid-keys)
# In production, these should be in environment variables
VAPID_PRIVATE_KEY = "38A2mLpIXczc-y5-2FSSTcZnHSU0nkp8CQ-iKK3ooP8"
VAPID_PUBLIC_KEY = "BKnGooPOu5u99TPhVIJoBzpApKs5gtfB_bHKS6z2-SxhHstN1BhWMxSQQc0cOyYG1mKCUH1UoOhj9N0IIMqafZuo"
VAPID_CLAIMS = {
    "sub": "mailto:admin@schoolquest.com"
}

class SubscriptionKeys(BaseModel):
    p256dh: str
    auth: str

class SubscriptionSchema(BaseModel):
    endpoint: str
    keys: SubscriptionKeys

@router.get("/vapid_public_key")
def get_vapid_public_key():
    return {"publicKey": VAPID_PUBLIC_KEY}

@router.post("/subscribe")
def subscribe(
    subscription: SubscriptionSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if subscription already exists
    existing_sub = db.query(PushSubscription).filter(
        PushSubscription.endpoint == subscription.endpoint
    ).first()

    if existing_sub:
        # Update user if changed (e.g. logout/login)
        if existing_sub.user_id != current_user.id:
            existing_sub.user_id = current_user.id
            db.commit()
        return {"message": "Subscription updated"}

    new_sub = PushSubscription(
        user_id=current_user.id,
        endpoint=subscription.endpoint,
        p256dh=subscription.keys.p256dh,
        auth=subscription.keys.auth
    )
    
    db.add(new_sub)
    db.commit()
    return {"message": "Subscribed successfully"}

@router.post("/send_test")
def send_test_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subs = db.query(PushSubscription).filter(PushSubscription.user_id == current_user.id).all()
    
    if not subs:
        raise HTTPException(status_code=404, detail="No subscriptions found for user")

    success_count = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                },
                data=json.dumps({
                    "title": "SchoolQuest",
                    "body": "Teste de notificação funcionando! 🚀",
                    "icon": "/pwa-192x192.png",
                    "url": "/"
                }),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            success_count += 1
        except WebPushException as ex:
            print(f"WebPush Error: {ex}")
            # Optionally remove invalid subscription
            # db.delete(sub)
            # db.commit()
        except Exception as e:
            print(f"Error sending notification: {e}")

    return {"message": f"Sent {success_count} notifications"}
