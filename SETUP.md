# Setup Guide — @pawfectchaos1

Same mechanism as `visual-versatility-autopost` (already live) and
`zaf-consultancy-post-images`. This is the third time this exact pattern
gets reused — the parts below marked "same as VV" are proven, not
guesswork.

## 0. Things only Theo can do (need his own Facebook/Meta login)

Claude cannot log into Meta on Theo's behalf, create the app-level
permissions, or generate tokens — those require Theo's own session. This
section is written for him to work through directly (in the browser, or
with Claude driving via Claude-in-Chrome while Theo does the actual
clicks/logins).

### 0a. Confirm @pawfectchaos1 is linked to a Facebook PAGE, not just your profile
The Graph API can only post through a Facebook **Page** linked to the
Instagram Business/Creator account — a personal profile isn't enough, even
if it shows up in the Instagram bio.
- Open Instagram app → pawfectchaos1 → Edit profile → Page.
- If no Page is linked yet: create one (Facebook → Pages → Create Page,
  e.g. "Pawfect Chaos" or similar), then link it from Instagram's Page
  settings.
- If a Page already exists and is linked, skip ahead.

### 0b. Reuse the existing Meta Developer app (don't create a new one)
The VV pipeline already has a working Meta app with the right permissions
(`instagram_basic`, `instagram_content_publish`, `pages_show_list`,
`pages_read_engagement`, `pages_manage_posts`). Reusing it avoids Meta's
app-review friction a second time.
- developers.facebook.com → My Apps → the app already used for VV.
- Business Settings → Accounts → Pages → **Add** → add the new
  pawfectchaos1 Page as an asset the app can access.

### 0c. Get the 4 secret values (identical steps to VV's SETUP.md)
In Graph API Explorer (developers.facebook.com → Tools → Graph API
Explorer), with the app from 0b and your access token selected:

1. **`GET me/accounts`** → find the pawfectchaos1 Page in the list.
   - Its `id` field = **`FB_PAGE_ID`**
2. **`GET {page-id}?fields=instagram_business_account`** → returns
   **`IG_USER_ID`**.
3. **Long-lived USER token**: exchange the short-lived Explorer token for
   a 60-day one by visiting (fill in your values, run it yourself, never
   paste the `client_secret` anywhere else):
   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}
   ```
   The response's `access_token` = **`IG_ACCESS_TOKEN`**.
4. **`FB_PAGE_TOKEN` is NOT the same value as `IG_ACCESS_TOKEN`** — this
   bit VV's own SETUP.md got wrong and it broke Facebook video posting
   here (`"(#100) No permission to publish the video"`, even with
   `publish_video` showing as a granted scope — `debug_token` on the
   reused value showed `"type": "USER"`, but Page actions need a
   Page-scoped token). Get the real one by running **`GET me/accounts`
   again**, this time using the long-lived USER token from step 3 as the
   Explorer's active token — the Page's `access_token` field in that
   response is a genuine long-lived Page token (`debug_token` on it
   should show `"type": "PAGE"`). That's your real `FB_PAGE_TOKEN`.

### 0d. Add the secrets to this GitHub repo
`osastdl/pawfectchaos-autopost` → Settings → Secrets and variables →
Actions → New repository secret. Add all 4: `IG_ACCESS_TOKEN`,
`IG_USER_ID`, `FB_PAGE_ID`, `FB_PAGE_TOKEN`.

## 1. What's already built (done, this session)

```
pawfectchaos-autopost/
├── scripts/
│   ├── autopost.py            -- calendar-driven poster (images/carousels)
│   └── manual_post_video.py   -- "once a video is made" -- post on demand
├── content/
│   ├── calendar.json          -- empty for now, [] -- add entries when
│   │                              there's a real posting queue
│   └── posted_log.json        -- filled in automatically as posts go out
├── .github/workflows/
│   ├── post.yml                -- cron-scheduled, reads calendar.json
│   └── manual-post-video.yml   -- workflow_dispatch: paste a video URL +
│                                   caption, it posts immediately
├── requirements.txt
└── README.md
```

## 2. Video must be at a PUBLIC url before posting

Same constraint as VV — Meta fetches the video (and photo) from a URL, it
can't read a private repo. **Resolved 2026-09-27**: rather than a separate
sibling images repo needing its own push token (VV's pattern), bot
uploads publish straight into `bot-uploads/` in THIS repo (already
public) via the workflow's own default `GITHUB_TOKEN` — no extra secret
needed. See `shared/github_publish.py`.

## 2b. The Telegram bot — how it actually works (built 2026-09-27)

`bot/main.py`, polled every 5 min by `.github/workflows/poll.yml`:

1. Send the bot a **photo or video** (as an attachment). It downloads it
   from Telegram, publishes it to `bot-uploads/` in this repo, drafts a
   caption (`shared/caption_generator.py`), and replies with the draft +
   a Post/Cancel keyboard.
2. Reply **"post"** or **"cancel"**. Confirming calls
   `destinations/pawfectchaos_fb_ig.py`, which posts to both Facebook and
   Instagram using the same 4 secrets `autopost.py` and
   `manual_post_video.py` already use (`IG_ACCESS_TOKEN`, `IG_USER_ID`,
   `FB_PAGE_ID`, `FB_PAGE_TOKEN`) — nothing new to configure.
3. For video, Instagram Reels processing is asynchronous — the bot polls
   for up to ~10 min after you confirm before it can actually publish, so
   the "posted" reply can take a few minutes to arrive. This reuses
   `manual_post_video.py`'s exact polling logic (that script's IG/FB
   posting code, unchanged); the bot just calls it from Telegram instead
   of requiring someone to manually run the Actions workflow with a
   pasted-in URL.
4. State (`content/offset.json`, `content/pending_posts.json`) is
   committed back to the repo by the workflow after every run — same
   pattern as `osastdl/atn-bot`'s bot, which this one's code structure is
   copied from (that one only supports photos; this one also does video).

**Before this date**, sending a video to any bot for this account did
nothing except (on atn-bot, a different bot entirely) reply "video
posting isn't wired up yet." No video pipeline existed anywhere for
Pawfect Chaos before 2026-09-27.

## 3. Test it

Once the 4 secrets are in place: Actions tab → "Manual video post" → **Run
workflow**, paste a public video URL + caption. Check the run log for
success or the exact Meta API error.

## 4. Ongoing maintenance
- Long-lived tokens expire after 60 days — repeat step 0c's exchange for
  `IG_ACCESS_TOKEN`, **then re-derive `FB_PAGE_TOKEN` fresh via
  `me/accounts`** using that new user token (don't just copy the user
  token into both secrets — see the note in step 0c.4).
- To pause posting entirely: Actions → the workflow → "..." → Disable
  workflow.
