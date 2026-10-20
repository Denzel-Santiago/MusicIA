import re


# These expressions intentionally cover only unmistakable video, lyrics, and
# publication labels. Musical descriptors such as "Remix" or "Radio Edit"
# are deliberately excluded.
VIDEO_NOISE_PATTERNS = (
    r"lyric(?:s)?(?:\s+video)?",
    r"official(?:\s+(?:video|audio))?",
    r"audio",
    r"hq",
    r"youtube",
)

LANGUAGE_NOISE_PATTERNS = (
    r"subtitulado\s+(?:al|en)\s+espa(?:n|\u00f1)ol",
    r"letra\s+en\s+espa(?:n|\u00f1)ol",
)

NOISE_PATTERN = "(?:" + "|".join(
    VIDEO_NOISE_PATTERNS + LANGUAGE_NOISE_PATTERNS
) + ")"

# "Official" by itself is only removed when it is a complete bracketed label.
# A phrase such as "Official New 2018" is too ambiguous to alter safely.
STANDALONE_NOISE_PATTERN_TEXT = "(?:" + "|".join(
    tuple(pattern for pattern in VIDEO_NOISE_PATTERNS if not pattern.startswith("official"))
    + LANGUAGE_NOISE_PATTERNS
) + ")"

# Trailing "By <uploader>" labels describe a publication, not the song.
ATTRIBUTION_PATTERNS = (
    re.compile(
        r"\s*\bby\s+[A-Za-z0-9_]+(?:[-_][A-Za-z0-9_]+)*\s*$",
        re.IGNORECASE,
    ),
    re.compile(r"\s*-\s*le7els\s+reco\s*$", re.IGNORECASE),
)

BRACKETED_NOISE_PATTERN = re.compile(
    r"\s*[\(\[\{\"\u201c\u201d]\s*"
    + NOISE_PATTERN
    + r"\s*[\)\]\}\"\u201c\u201d]\s*",
    re.IGNORECASE,
)
STANDALONE_NOISE_PATTERN = re.compile(
    r"\b" + STANDALONE_NOISE_PATTERN_TEXT + r"\b",
    re.IGNORECASE,
)
EMPTY_BRACKETS_PATTERN = re.compile(r"[\(\[\{]\s*[\)\]\}]")
EMPTY_QUOTES_PATTERN = re.compile(r"[\"\u201c\u201d]\s*[\"\u201c\u201d]")


def clean_title(title):
    """Return a conservative normalized title without changing the input."""
    if not title:
        return None

    cleaned = str(title).strip()

    # Remove complete noise labels before processing bare occurrences so their
    # brackets and quotes do not remain in the final title.
    cleaned = BRACKETED_NOISE_PATTERN.sub(" ", cleaned)
    cleaned = STANDALONE_NOISE_PATTERN.sub("", cleaned)
    cleaned = re.sub(
        r"\s*[-|/\u2013\u2014\u00e2\u0080\u0093\u00e2\u0080\u0094]+\s*([\)\]\}])",
        r"\1",
        cleaned,
    )

    for pattern in ATTRIBUTION_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    cleaned = re.sub(r"\s*//\s*", " ", cleaned)
    cleaned = EMPTY_BRACKETS_PATTERN.sub("", cleaned)
    cleaned = EMPTY_QUOTES_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Remove only separators made dangling by a removed noise label. Do not
    # touch internal dashes, which can separate valid artists or mix names.
    cleaned = re.sub(r"^(?:\s*[-|/]\s*)+", "", cleaned)
    cleaned = re.sub(r"(?:\s*[-|/]\s*)+$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned or None


def clean_metadata(metadata):
    """Clean interpreted metadata while preserving the original values."""
    return {
        "title": clean_title(metadata.get("title")),
        "artist": metadata.get("artist"),
    }


def clean_resolved_metadata(metadata):
    """Return resolved metadata with only its interpreted title cleaned."""
    cleaned_metadata = dict(metadata)
    cleaned_metadata["title"] = clean_metadata(metadata)["title"]
    return cleaned_metadata


if __name__ == "__main__":
    tests = (
        ("The Nights", "The Nights"),
        ("The Nights (Lyric Video)", "The Nights"),
        ("Waiting For Love (Lyrics)", "Waiting For Love"),
        ("Lonely Together \u201cAudio\u201d ft. Rita Ora", "Lonely Together ft. Rita Ora"),
        ("SOS ft. Aloe Blacc // Subtitulado al espa\u00f1ol //", "SOS ft. Aloe Blacc"),
        (
            "Let Me Show You Love (Letra En Espa\u00f1ol) By Avicii_Fans_Lyrics",
            "Let Me Show You Love",
        ),
        ("Fade Into Darkness (Official Video) - Le7els Reco", "Fade Into Darkness"),
        ("Without You \u201cAudio\u201d ft. Sandro Cavazza", "Without You ft. Sandro Cavazza"),
        ("I Could Be The One - Nicktim - Radio Edit", "I Could Be The One - Nicktim - Radio Edit"),
        ("Without You (AFISHAL Remix)", "Without You (AFISHAL Remix)"),
        ("For A Better Day (KSHMR Remix)", "For A Better Day (KSHMR Remix)"),
        ("Levels - Original Mix", "Levels - Original Mix"),
        ("Wake Me Up - Acoustic Version", "Wake Me Up - Acoustic Version"),
        ("The Nights - Radio Edit", "The Nights - Radio Edit"),
        ("Some Song - Club Mix", "Some Song - Club Mix"),
        ("Song Title (Live Version)", "Song Title (Live Version)"),
        ("Song Title feat. Artist", "Song Title feat. Artist"),
        ("Song Title ft. Artist", "Song Title ft. Artist"),
    )

    for title, expected in tests:
        result = clean_title(title)
        status = "OK" if result == expected else "ERROR"

        print("\n-----------------------------")
        print(f"Original: {title}")
        print(f"Limpio:   {result}")
        print(f"Resultado: {status}")
