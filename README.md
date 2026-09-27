# pawfectchaos-autopost
Automated Instagram + Facebook posting for @pawfectchaos1, via Meta Graph API. Two live paths:

- **Telegram bot** (`bot/`, `.github/workflows/poll.yml`) — send a photo or video to the bot, confirm the drafted caption, it posts to Facebook + Instagram. This is the main day-to-day path. See `SETUP.md` for how it works end to end.
- **Calendar-driven** (`scripts/autopost.py`, `.github/workflows/post.yml`) — for a scheduled content queue in `content/calendar.json`, images only. Unused so far (`calendar.json` is empty).

`scripts/manual_post_video.py` (ad-hoc video via `workflow_dispatch`) still exists but is superseded by the bot for normal use — the bot's `destinations/pawfectchaos_fb_ig.py` reuses its exact Instagram Reels + Facebook video logic.
