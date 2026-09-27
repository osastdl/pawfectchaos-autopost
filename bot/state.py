"""Persists bot state (Telegram update offset, pending post confirmations)
to committed JSON files, since the bot runs as a scheduled CI job with no
long-lived memory between runs -- same pattern as atn-bot's bot/state.py.
The workflow that invokes bot/main.py is responsible for committing any
changes these functions write back to disk.
"""

import json
import os
import uuid

CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content")
OFFSET_PATH = os.path.join(CONTENT_DIR, "offset.json")
PENDING_PATH = os.path.join(CONTENT_DIR, "pending_posts.json")


def get_offset():
    with open(OFFSET_PATH) as f:
        return json.load(f)["offset"]


def set_offset(offset):
    with open(OFFSET_PATH, "w") as f:
        json.dump({"offset": offset}, f)


def load_pending():
    with open(PENDING_PATH) as f:
        return json.load(f)


def save_pending(pending):
    with open(PENDING_PATH, "w") as f:
        json.dump(pending, f, indent=2)


def add_pending(entry):
    pending = load_pending()
    short_id = uuid.uuid4().hex[:8]
    pending[short_id] = entry
    save_pending(pending)
    return short_id


def pop_pending(short_id):
    pending = load_pending()
    entry = pending.pop(short_id, None)
    save_pending(pending)
    return entry


def find_pending_by_message_id(message_id):
    """Correlates a reply back to the pending entry it's replying to."""
    pending = load_pending()
    for short_id, entry in pending.items():
        if entry.get("message_id") == message_id:
            return short_id, entry
    return None, None


def find_oldest_pending(chat_id):
    """Fallback when a "post"/"cancel" isn't sent as an actual Telegram
    reply (common -- clients vary, users don't always use the gesture).
    Dict preserves insertion order, so the first match is the oldest."""
    pending = load_pending()
    for short_id, entry in pending.items():
        if entry.get("chat_id") == chat_id:
            return short_id, entry
    return None, None
