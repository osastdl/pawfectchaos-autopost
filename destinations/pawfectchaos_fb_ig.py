"""Posts to @pawfectchaos1's real Facebook Page + Instagram Business
account via the Meta Graph API.

Reuses the exact same 4 secrets already configured and proven for this
repo's other two posting paths (scripts/autopost.py for images,
scripts/manual_post_video.py for ad-hoc videos) -- IG_ACCESS_TOKEN,
IG_USER_ID, FB_PAGE_ID, FB_PAGE_TOKEN. No new credentials needed.

Photo flow (post_photo): Facebook accepts a direct photo POST; Instagram's
image container is ready immediately -- no polling needed (confirmed by
the ZAF Consultancy destination this pattern was copied from, and by the
one real photo this account has already posted, 2026-09-16).

Video flow (post_video): Facebook accepts a direct video POST too, but
Instagram Reels needs a container created, then polled (up to ~10 min)
until Meta finishes processing before it can be published -- this is
scripts/manual_post_video.py's already-working logic, moved here so the
Telegram bot (bot/main.py) can call it the same way it calls post_photo,
instead of only being reachable via a manually-triggered GitHub Action.
"""

import os
import time

import requests

GRAPH_API = "https://graph.facebook.com/v21.0"


def _config():
    return {
        "ig_access_token": os.environ["IG_ACCESS_TOKEN"],
        "ig_user_id": os.environ["IG_USER_ID"],
        "fb_page_id": os.environ["FB_PAGE_ID"],
        "fb_page_token": os.environ["FB_PAGE_TOKEN"],
    }


def _check(resp, what):
    data = resp.json()
    if "error" in data or resp.status_code >= 400:
        raise RuntimeError(f"{what} failed: {data}")
    return data


def _permalink(object_id, field, token):
    data = _check(
        requests.get(
            f"{GRAPH_API}/{object_id}",
            params={"fields": field, "access_token": token},
        ),
        "permalink lookup",
    )
    return data.get(field)


def post_to_facebook_photo(image_url, caption):
    cfg = _config()
    result = _check(
        requests.post(
            f"{GRAPH_API}/{cfg['fb_page_id']}/photos",
            data={"url": image_url, "caption": caption, "access_token": cfg["fb_page_token"]},
        ),
        "Facebook photo post",
    )
    post_id = result["post_id"]
    permalink = _permalink(post_id, "permalink_url", cfg["fb_page_token"])
    return {"id": post_id, "url": permalink}


def post_to_instagram_photo(image_url, caption):
    cfg = _config()
    container = _check(
        requests.post(
            f"{GRAPH_API}/{cfg['ig_user_id']}/media",
            data={"image_url": image_url, "caption": caption, "access_token": cfg["ig_access_token"]},
        ),
        "Instagram photo container",
    )
    creation_id = container["id"]

    # Static images (unlike video/reels) are ready immediately -- querying
    # status_code right after creation is a known source of a spurious
    # "object does not exist" 400, so don't (same note as zaf_consultancy).
    published = _check(
        requests.post(
            f"{GRAPH_API}/{cfg['ig_user_id']}/media_publish",
            data={"creation_id": creation_id, "access_token": cfg["ig_access_token"]},
        ),
        "Instagram photo publish",
    )
    media_id = published["id"]
    permalink = _permalink(media_id, "permalink", cfg["ig_access_token"])
    return {"id": media_id, "url": permalink}


def post_to_facebook_video(video_url, caption):
    cfg = _config()
    result = _check(
        requests.post(
            f"{GRAPH_API}/{cfg['fb_page_id']}/videos",
            data={"file_url": video_url, "description": caption, "access_token": cfg["fb_page_token"]},
        ),
        "Facebook video post",
    )
    video_id = result["id"]
    permalink = _permalink(video_id, "permalink_url", cfg["fb_page_token"])
    return {"id": video_id, "url": permalink or f"https://facebook.com/{video_id}"}


def post_to_instagram_video(video_url, caption):
    cfg = _config()
    container = _check(
        requests.post(
            f"{GRAPH_API}/{cfg['ig_user_id']}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": cfg["ig_access_token"],
            },
        ),
        "Instagram Reels container",
    )
    creation_id = container["id"]

    # Video processing is asynchronous -- poll status_code until FINISHED
    # before publishing. Up to ~10 min at 10s intervals, same budget
    # already proven in scripts/manual_post_video.py; a GitHub Actions job
    # has plenty of runtime for this, unlike a normal web request.
    for _ in range(60):
        time.sleep(10)
        status = _check(
            requests.get(
                f"{GRAPH_API}/{creation_id}",
                params={"fields": "status_code", "access_token": cfg["ig_access_token"]},
            ),
            "Instagram Reels status check",
        )
        code = status.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"Instagram Reels processing failed: {status}")
    else:
        raise RuntimeError("Instagram Reels processing timed out after 10 minutes")

    published = _check(
        requests.post(
            f"{GRAPH_API}/{cfg['ig_user_id']}/media_publish",
            data={"creation_id": creation_id, "access_token": cfg["ig_access_token"]},
        ),
        "Instagram Reels publish",
    )
    media_id = published["id"]
    permalink = _permalink(media_id, "permalink", cfg["ig_access_token"])
    return {"id": media_id, "url": permalink}


def post_photo(image_url, caption):
    return {
        "facebook": post_to_facebook_photo(image_url, caption),
        "instagram": post_to_instagram_photo(image_url, caption),
    }


def post_video(video_url, caption):
    return {
        "facebook": post_to_facebook_video(video_url, caption),
        "instagram": post_to_instagram_video(video_url, caption),
    }


def post(media_url, caption, media_type):
    """media_type: 'photo' or 'video' -- dispatches to the right flow.
    Kept as one entrypoint so callers (bot/main.py) don't need an if/else
    of their own."""
    if media_type == "video":
        return post_video(media_url, caption)
    return post_photo(media_url, caption)
