import logging
import os
import requests
from wagtail.signals import page_published, page_unpublished

from .models import ArticlePage

logger = logging.getLogger(__name__)


def trigger_pages_build(**kwargs):
    url = os.getenv("CLOUDFLARE_BUILD_HOOK")
    if not url:
        return
    try:
        requests.post(url, timeout=10)
    except requests.RequestException as exc:
        logger.warning("Pages build hook failed: %s", exc)


def notify_buttondown(**kwargs):
    api_key = os.getenv("BUTTONDOWN_API_KEY")
    if not api_key:
        return
    page = kwargs.get("page") or kwargs.get("instance")
    if page is None or not isinstance(page, ArticlePage):
        return
    title = page.title
    slug = page.slug
    base = os.getenv("FRONTEND_URL", "https://tinta-pausa.pages.dev")
    post_url = f"{base}/archive/{slug}/"
    body = f"# {title}\n\n"
    if page.image:
        image_url = page.image.get_rendition("width-800").url
        body += f'<img src="{image_url}" alt="{title}" style="max-width:100%;height:auto;" />\n\n'
    body += (
        f"Se publicó un nuevo artículo **{title}**.\n\nLéelo aquí: [{slug}]({post_url})"
    )
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    try:
        # Step 1: Create email as draft
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
                "Buttondown draft creation failed: %s %s",
                resp.status_code,
                resp.text,
            )
            return

        email_id = resp.json().get("id")
        if not email_id:
            logger.warning("Buttondown draft response missing id: %s", resp.text)
            return

        # Step 2: Send the draft
        resp = requests.patch(
            f"https://api.buttondown.com/v1/emails/{email_id}",
            headers=headers,
            json={"status": "about_to_send"},
            timeout=10,
        )
        if not resp.ok:
            logger.warning(
                "Buttondown send failed: %s %s",
                resp.status_code,
                resp.text,
            )
    except requests.RequestException as exc:
        logger.warning("Buttondown notify failed: %s", exc)


def on_article_published(**kwargs):
    page = kwargs.get("page") or kwargs.get("instance")
    if page is None or not isinstance(page, ArticlePage):
        return
    trigger_pages_build(**kwargs)
    notify_buttondown(**kwargs)


def on_article_unpublished(**kwargs):
    page = kwargs.get("page") or kwargs.get("instance")
    if page is None or not isinstance(page, ArticlePage):
        return
    trigger_pages_build(**kwargs)


page_published.connect(on_article_published)
page_unpublished.connect(on_article_unpublished)
