import logging
import os
import requests
from wagtail.signals import page_published
from .models import ArticlePage

logger = logging.getLogger(name)


def notify_buttondown(**kwargs):
    api_key = os.getenv("BUTTONDOWN_API_KEY")
    if not api_key:
        return
    page = kwargs.get("page") or kwargs.get("instance")
    if page is None or not isinstance(page, ArticlePage):
        return
    title = page.title
    slug = page.slug
    base = os.getenv("FRONTEND_URL", "http://localhost:4321")
    post_url = f"{base}/archive/{slug}/"
    body = f"# {title}\n\n"
    if page.image:
        image_url = page.image.get_rendition("width-800").url
        body += f'<img src="{image_url}" alt="{title}" style="max-width:100%;height:auto;" />\n\n'
    body += f"Se publicó un nuevo artículo: {title}.\n\nLéelo aquí: {slug}"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(
            "https://api.buttondown.com/v1/emails",
            headers=headers,
            json={
                "subject": f"Nuevo artículo: {title}",
                "body": body,
                "status": "draft",
            },
            timeout=10,
        )
        if not resp.ok:
            logger.warning(
                "Buttondown draft failed: %s %s", resp.status_code, resp.text
            )
            return
        email_id = resp.json().get("id")
        if not email_id:
            return
        resp = requests.patch(
            f"https://api.buttondown.com/v1/emails/{email_id}",
            headers=headers,
            json={"status": "about_to_send"},
            timeout=10,
        )
        if not resp.ok:
            logger.warning("Buttondown send failed: %s %s", resp.status_code, resp.text)
    except requests.RequestException as exc:
        logger.warning("Buttondown notify failed: %s", exc)


def on_article_published(**kwargs):
    notify_buttondown(**kwargs)


page_published.connect(on_article_published)
