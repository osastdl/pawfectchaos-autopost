"""Template-based caption + hashtag generation for @pawfectchaos1 -- same
proven approach as atn-bot's shared/caption_generator.py and VV Outreach's
poster.py before it, not a vision/AI API call. No external dependency, no
billing, works right now.

Whatever caption you type alongside the photo/video on Telegram gets
folded in as `hint` -- same mechanism as the other two bots, so you can
still add your own write-up any time you want to.
"""

import random

_CAPTION_OPENERS = [
    "Pure, unfiltered chaos. \U0001F436\n\n{hint}",
    "Another day, another questionable life choice. \U0001F43E\n\n{hint}",
    "Certified good boy/girl behaviour (mostly). ✅\n\n{hint}",
    "Living their best (and loudest) life. \U0001F60A\n\n{hint}",
    "This is the content you signed up for. \U0001F3AC\n\n{hint}",
    "Zero regrets, as usual. \U0001F602\n\n{hint}",
    "Pawfect chaos, as advertised. \U0001F43E\n\n{hint}",
    "Some days you're the human, some days you're just staff. \U0001F644\n\n{hint}",
    "Ten out of ten, no notes. ⭐\n\n{hint}",
    "The main character energy is unmatched. \U0001F31F\n\n{hint}",
    "Filed under: things I didn't plan for today. \U0001F4C2\n\n{hint}",
    "Chaos level: expert. \U0001F3C6\n\n{hint}",
    "Just another Tuesday in this house. \U0001F3E0\n\n{hint}",
    "Proof that good things come in fur coats. \U0001F9E5\n\n{hint}",
    "This one's staying in the highlight reel. \U0001F4F8\n\n{hint}",
    "Caught in the act, as always. \U0001F440\n\n{hint}",
    "No thoughts, just vibes. \U0001F4AD\n\n{hint}",
    "The audacity. The confidence. Love it. \U0001F602\n\n{hint}",
    "Sharing this before I forget how funny it was. \U0001F923\n\n{hint}",
    "A public service announcement from the dog. \U0001F4E3\n\n{hint}",
]

_HASHTAG_POOL = [
    "#PawfectChaos", "#DogsOfInstagram", "#DogLife", "#DogVideo",
    "#GoodBoy", "#GoodGirl", "#DogMom", "#DogDad", "#FunnyDogs",
    "#DogReels", "#DogsBeingDogs", "#PetContentCreator", "#DailyDog",
    "#DogPersonality", "#DogAntics", "#InstaDog", "#DogTok",
    "#RescueDog", "#DogLovers", "#PawsomeContent",
]


def generate_caption(hint_text=None):
    """hint_text is whatever caption the sender typed alongside the
    photo/video on Telegram -- folded into a template rather than posted
    bare, same mechanism as the ZAF/VV bots."""
    opener = random.choice(_CAPTION_OPENERS)
    hint = (hint_text or "").strip()
    body = opener.format(hint=hint) if hint else opener.replace("{hint}\n\n", "").replace("{hint}", "")
    body = body.rstrip()

    tags = " ".join(random.sample(_HASHTAG_POOL, k=random.randint(5, 6)))
    return f"{body}\n\n{tags}"
