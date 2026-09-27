"""Pawfect Chaos bot entrypoint.

Runs as ONE poll pass per invocation -- meant to be triggered by a
scheduled GitHub Actions job every ~5 minutes, not run as a standalone
long-lived loop. State (Telegram offset, pending post confirmations)
persists to content/*.json between runs; the calling workflow commits
those files back to the repo after each run. Pattern (and most of this
file) copied from atn-bot's bot/main.py -- proven there since 2026-08-18.

Photo AND video both work here, unlike atn-bot: send a photo or a video
-> generate a caption from a template pool -> publish it publicly (into
THIS repo's own bot-uploads/ folder, see shared/github_publish.py) ->
reply "post" or "cancel" to confirm before it goes out to Facebook and
Instagram. Deliberately NOT inline buttons -- same reasoning as atn-bot:
Telegram callback queries expire within seconds, a ~5-minute poll cycle
can never catch one in time. Also deliberately not requiring an actual
Telegram reply-to-message -- not every client reliably sends that as
real reply data, so "post"/"cancel" just resolves to the oldest pending
post for that chat instead.

Any video already sitting in this bot's Telegram queue from before this
was wired up (Telegram keeps unread bot updates ~24h) gets picked up and
processed on the very first poll run after this deploys, exactly like any
new upload -- there's no separate backlog step.
"""

import html
import os
import uuid

from bot import state
from destinations import pawfectchaos_fb_ig
from shared import caption_generator, github_publish, telegram_api

MEDIA_REPO = "osastdl/pawfectchaos-autopost"

WELCOME = (
    "<b>\U0001F436 Pawfect Chaos bot is online</b>\n\n"
    "Send me a photo or a video (as an attachment, not a link) -- I'll "
    "draft a caption and ask you to confirm before it goes to Facebook "
    "and Instagram."
)

NOTHING_PENDING = "\U0001F937 Nothing pending to confirm right now."

UNRECOGNIZED = "Not sure what you mean -- send a photo or video to post it, or tap the button below."

BOT_COMMANDS = [
    {"command": "start", "description": "Show the menu"},
]


def handle_start(message):
    telegram_api.send_message(
        message["chat"]["id"], WELCOME, parse_mode="HTML",
        reply_markup=telegram_api.PERSISTENT_KEYBOARD,
    )


def _stage_media(message, *, telegram_file_id, ext, media_type):
    """Shared by handle_photo/handle_video: download from Telegram,
    publish publicly, draft a caption, record it as pending, and send the
    confirmation prompt back. Returns nothing -- all side effects."""
    chat_id = message["chat"]["id"]
    file_path = telegram_api.get_file_path(telegram_file_id)
    media_bytes = telegram_api.download_file(file_path)

    full_caption = caption_generator.generate_caption(hint_text=message.get("caption"))

    repo_path = f"bot-uploads/{uuid.uuid4().hex}.{ext}"
    media_url = github_publish.publish(
        token=os.environ["GITHUB_TOKEN"],
        repo=MEDIA_REPO,
        path=repo_path,
        content_bytes=media_bytes,
        message="Bot upload pending confirmation",
    )

    short_id = state.add_pending(
        {
            "media_url": media_url,
            "media_type": media_type,
            "file_id": telegram_file_id,
            "caption": full_caption,
        }
    )

    send = telegram_api.send_video if media_type == "video" else telegram_api.send_photo
    note = (
        "\U0001F3AC Video processing on Instagram can take a few minutes "
        "after you confirm -- I'll message again once it's live."
        if media_type == "video"
        else ""
    )
    sent = send(
        chat_id,
        **{media_type: telegram_file_id},
        caption=(
            f"\U0001F4DD <b>Draft caption</b>\n\n{html.escape(full_caption)}\n\n"
            f"<i>Tap Post or Cancel below.{(' ' + note) if note else ''}</i>"
        ),
        parse_mode="HTML",
        reply_markup=telegram_api.CONFIRM_KEYBOARD,
    )

    pending = state.load_pending()
    pending[short_id]["chat_id"] = chat_id
    pending[short_id]["message_id"] = sent["result"]["message_id"]
    state.save_pending(pending)


def handle_photo(message):
    file_id = message["photo"][-1]["file_id"]  # largest size
    _stage_media(message, telegram_file_id=file_id, ext="jpg", media_type="photo")


def handle_video(message):
    file_id = message["video"]["file_id"]
    _stage_media(message, telegram_file_id=file_id, ext="mp4", media_type="video")


def handle_reply_confirmation(message):
    chat_id = message["chat"]["id"]
    action = message["text"].strip().lower()

    short_id, entry = None, None
    if "reply_to_message" in message:
        short_id, entry = state.find_pending_by_message_id(message["reply_to_message"]["message_id"])
    if entry is None:
        short_id, entry = state.find_oldest_pending(chat_id)
    if entry is None:
        telegram_api.send_message(chat_id, NOTHING_PENDING)
        return

    state.pop_pending(short_id)
    send = telegram_api.send_video if entry["media_type"] == "video" else telegram_api.send_photo

    if action == "cancel":
        send(
            chat_id,
            **{entry["media_type"]: entry["file_id"]},
            caption="\U0001F6AB <b>Cancelled</b> -- not posted.",
            parse_mode="HTML",
            reply_markup=telegram_api.PERSISTENT_KEYBOARD,
        )
        return

    if entry["media_type"] == "video":
        telegram_api.send_message(
            chat_id,
            "⏳ Posting the video now -- Instagram processing can take "
            "a few minutes, hang tight.",
        )

    print(f"Posting {entry['media_type']} ({entry['media_url']}) for chat {chat_id}...")
    try:
        result = pawfectchaos_fb_ig.post(entry["media_url"], entry["caption"], entry["media_type"])
        print(f"  Facebook: {result['facebook']}")
        print(f"  Instagram: {result['instagram']}")
        state.log_posted(entry, result)
        fb_url = html.escape(result["facebook"]["url"])
        ig_url = html.escape(result["instagram"]["url"])
        send(
            chat_id,
            **{entry["media_type"]: entry["file_id"]},
            caption=(
                "<b>✅ Posted successfully</b>\n\n"
                f'\U0001F4D8 <a href="{fb_url}">View on Facebook</a>\n'
                f'\U0001F4F7 <a href="{ig_url}">View on Instagram</a>'
            ),
            parse_mode="HTML",
            reply_markup=telegram_api.PERSISTENT_KEYBOARD,
        )
    except Exception as e:
        print(f"  FAILED: {e}")
        send(
            chat_id,
            **{entry["media_type"]: entry["file_id"]},
            caption=f"❌ <b>Failed to post</b>\n\n{html.escape(str(e))}",
            parse_mode="HTML",
            reply_markup=telegram_api.PERSISTENT_KEYBOARD,
        )


def handle_message(message):
    text = message.get("text", "").strip().lower()
    if text in ("post", "cancel"):
        handle_reply_confirmation(message)
    elif "photo" in message:
        handle_photo(message)
    elif "video" in message:
        handle_video(message)
    elif text.startswith("/start") or text == "\U0001F436 post content":
        handle_start(message)
    else:
        telegram_api.send_message(
            message["chat"]["id"], UNRECOGNIZED,
            reply_markup=telegram_api.PERSISTENT_KEYBOARD,
        )


def poll_once():
    telegram_api.set_my_commands(BOT_COMMANDS)
    me = telegram_api.get_me()["result"]
    offset = state.get_offset()
    result = telegram_api.get_updates(offset=offset, timeout=5)
    updates = result.get("result", [])
    # Plain diagnostic, no secrets -- bot identity + queue size are the two
    # things worth seeing in the Actions log when something seems stuck.
    print(f"Bot: @{me.get('username')} ({me.get('first_name')}) -- offset={offset}, {len(updates)} update(s) waiting")
    for update in updates:
        kinds = [k for k in ("photo", "video", "text") if k in update.get("message", {})]
        print(f"  update {update['update_id']}: {kinds or list(update.keys())}")

    for update in updates:
        state.set_offset(update["update_id"] + 1)
        if "message" in update:
            handle_message(update["message"])


if __name__ == "__main__":
    poll_once()
