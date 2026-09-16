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
   - Its `access_token` field = **`FB_PAGE_TOKEN`**
2. **`GET {page-id}?fields=instagram_business_account`** → returns
   **`IG_USER_ID`**.
3. **Long-lived token**: exchange the short-lived Explorer token for a
   60-day one by visiting (fill in your values, run it yourself, never
   paste the `client_secret` anywhere else):
   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}
   ```
   The response's `access_token` = **`IG_ACCESS_TOKEN`** (reuse the same
   value for `FB_PAGE_TOKEN` too, unless you want a separately-scoped Page
   token).

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

Same constraint as VV — Meta fetches the video from a URL, it can't read a
private repo. Either:
- push finished dog videos to a **public** repo (mirroring
  `visual-versatility-post-images`), or
- host them anywhere else public (a public GitHub release asset, etc.)

Not built yet — say the word once you're ready and this gets the same
treatment as VV's image repo.

## 3. Test it

Once the 4 secrets are in place: Actions tab → "Manual video post" → **Run
workflow**, paste a public video URL + caption. Check the run log for
success or the exact Meta API error.

## 4. Ongoing maintenance
- Long-lived tokens expire after 60 days — repeat step 0c's exchange and
  update the secret.
- To pause posting entirely: Actions → the workflow → "..." → Disable
  workflow.
