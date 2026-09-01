import hmac
import hashlib
import json
import os
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import NewsletterSubscriber


@csrf_exempt
@require_POST
def buttondown_webhook(request):
    secret = os.getenv("BUTTONDOWN_WEBHOOK_SECRET")
    api_key = os.getenv("BUTTONDOWN_API_KEY")
    if not secret or not api_key:
        return HttpResponse(status=500)

    header = request.headers.get("X-Buttondown-Signature", "")
    if not verify_signature(request.body, header, secret):
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if payload.get("event_type") != "subscriber.confirmed":
        return HttpResponse(status=204)

    subscriber_id = (payload.get("data") or {}).get("subscriber")
    if not subscriber_id:
        return HttpResponse(status=400)

    resp = requests.get(
        f"https://api.buttondown.com/v1/subscribers/{subscriber_id}",
        headers={"Authorization": f"Token {api_key}"},
        timeout=10,
    )
    if not resp.ok:
        return HttpResponse(status=502)

    data = resp.json()
    email = data.get("email_address")
    name = (data.get("metadata") or {}).get("name") or ""
    if not email:
        return HttpResponse(status=400)

    NewsletterSubscriber.objects.update_or_create(
        email=email,
        defaults={"name": name},
    )
    return HttpResponse(status=204)


def verify_signature(payload, signature_header, signing_key):
    signature = signature_header.replace("sha256=", "")
    mac = hmac.new(
        signing_key.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    )
    return hmac.compare_digest(signature, mac.hexdigest())
