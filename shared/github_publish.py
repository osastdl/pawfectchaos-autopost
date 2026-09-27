"""Publishes a file to a public GitHub repo via the Contents API, so Meta's
Graph API has a public URL to fetch from -- same pattern as atn-bot's
shared/github_publish.py.

Unlike atn-bot (which pushes to a separate image-hosting repo via a
dedicated IMAGE_REPO_TOKEN secret), this publishes straight into THIS
repo's own `bot-uploads/` folder using the workflow's default
GITHUB_TOKEN. `osastdl/pawfectchaos-autopost` is already public, so no
extra secret or separate repo is needed for bot-sourced media to get a
working raw.githubusercontent.com URL. Branch is `master` here (this
repo's default), not `main` -- don't copy atn-bot's hardcoded value.
"""

import base64
import json
import urllib.request


def publish(token, repo, path, content_bytes, message, branch="master"):
    """repo: 'owner/name'. Returns the raw.githubusercontent.com URL."""
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    body = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("ascii"),
        "branch": branch,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        method="PUT",
    )
    with urllib.request.urlopen(req) as resp:
        json.loads(resp.read().decode("utf-8"))

    return f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
