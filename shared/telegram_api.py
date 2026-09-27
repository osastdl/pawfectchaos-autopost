"""Raw urllib Telegram Bot API wrapper -- no python-telegram-bot dependency.
Same pattern already proven in atn-bot's shared/telegram_api.py; copied
here (not imported cross-repo) because this repo has its own
TELEGRAM_BOT_TOKEN -- a separate bot from ATN's, tied to @pawfectchaos1.
"""

import json
import os
import urllib.error
import urllib.request

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _token():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    return token


def call(method, **params):
    url = API_BASE.format(token=_token(), method=method)
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Telegram API error {e.code}: {e.read().decode('utf-8')}") from None


def get_me():
    return call("getMe")


def get_updates(offset=None, timeout=30):
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    return call("getUpdates", **params)


def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    params = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        params["reply_markup"] = reply_markup
    if parse_mode is not None:
        params["parse_mode"] = parse_mode
    return call("sendMessage", **params)


def send_photo(chat_id, photo, caption=None, parse_mode=None, reply_markup=None):
    """photo can be a Telegram file_id (reuse what was already uploaded --
    no need to re-fetch/re-send the bytes) or a public URL."""
    params = {"chat_id": chat_id, "photo": photo}
    if caption is not None:
        params["caption"] = caption
    if parse_mode is not None:
        params["parse_mode"] = parse_mode
    if reply_markup is not None:
        params["reply_markup"] = reply_markup
    return call("sendPhoto", **params)


def send_video(chat_id, video, caption=None, parse_mode=None, reply_markup=None):
    """video can be a Telegram file_id or a public URL -- mirrors send_photo."""
    params = {"chat_id": chat_id, "video": video}
    if caption is not None:
        params["caption"] = caption
    if parse_mode is not None:
        params["parse_mode"] = parse_mode
    if reply_markup is not None:
        params["reply_markup"] = reply_markup
    return call("sendVideo", **params)


def set_my_commands(commands):
    """commands: [{"command": "start", "description": "..."}, ...] --
    populates the tappable "/" menu next to the message box. Cheap and
    idempotent, safe to call every poll run."""
    return call("setMyCommands", commands=commands)


# Every core action visible as a tap -- nothing relies on knowing a "/"
# command exists.
PERSISTENT_KEYBOARD = {
    "keyboard": [["\U0001F43E Post content"]],
    "resize_keyboard": True,
    "is_persistent": True,
}

# "post"/"cancel" are fixed strings, so real tappable buttons work fine
# here -- unlike inline keyboards (callback queries), a reply-keyboard tap
# just sends its label as a normal text message, no expiry problem. A
# ~5-minute poll cycle can never catch an inline callback query in time
# (it expires within seconds) -- confirmed the hard way in atn-bot.
CONFIRM_KEYBOARD = {
    "keyboard": [["post", "cancel"]],
    "resize_keyboard": True,
    "one_time_keyboard": True,
}


def get_file_path(file_id):
    return call("getFile", file_id=file_id)["result"]["file_path"]


def download_file(file_path):
    url = f"https://api.telegram.org/file/bot{_token()}/{file_path}"
    with urllib.request.urlopen(url) as resp:
        return resp.read()
