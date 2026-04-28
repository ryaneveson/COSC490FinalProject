"""Shared constants and helpers for the password analysis scripts."""

import re

__all__ = [
    "LEET_REPLACEMENTS",
    "WORD_CATEGORIES",
    "KEYBOARD_ROWS",
    "COMMON_KEYBOARD_PATTERNS",
    "PATTERN_TYPE_PENALTIES",
    "SPECIFIC_SEQUENCE_PATTERNS",
    "GRADE_THRESHOLDS",
    "normalize_leet",
    "extract_tokens",
    "has_keyboard_pattern",
]


# ============================================================================
# Shared Constants (used in both step4 and step6)
# ============================================================================

LEET_REPLACEMENTS = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
    "9": "g",
    "@": "a",
    "$": "s",
    "!": "i",
    "+": "t",
}

WORD_CATEGORIES = {
    "names": {
        "john",
        "mike",
        "david",
        "james",
        "mary",
        "anna",
        "maria",
        "alex",
        "ryan",
        "emma",
        "liam",
    },
    "nouns": {
        "password",
        "dragon",
        "monkey",
        "football",
        "baseball",
        "shadow",
        "master",
        "sunshine",
        "hello",
        "freedom",
        "qwerty",
    },
    "verbs": {
        "love",
        "login",
        "letmein",
        "trust",
        "run",
        "jump",
        "start",
        "enter",
        "pass",
        "play",
    },
    "adjectives": {
        "super",
        "cool",
        "secure",
        "happy",
        "fast",
        "strong",
        "smart",
        "dark",
        "light",
        "best",
    },
    "places": {
        "london",
        "paris",
        "tokyo",
        "berlin",
        "madrid",
        "rome",
        "canada",
        "usa",
        "india",
        "china",
    },
    "dates": {
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
        "year",
        "today",
    },
}

KEYBOARD_ROWS = [
    "1234567890",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
]

COMMON_KEYBOARD_PATTERNS = {
    "qwerty",
    "asdf",
    "zxcv",
    "1234",
    "12345",
    "123456",
    "qaz",
    "wsx",
    "edc",
    "poiuy",
}


# ============================================================================
# Step 6 Specific Constants
# ============================================================================

PATTERN_TYPE_PENALTIES = {
    "dictionary_lookup": 8,
    "l33t_detection": 4,
    "keyboard_pattern": 12,
    "word_category:names": 10,
    "word_category:nouns": 9,
    "word_category:verbs": 8,
    "word_category:adjectives": 6,
    "word_category:places": 6,
    "word_category:dates": 7,
}

SPECIFIC_SEQUENCE_PATTERNS = {
    "qwerty": 10,
    "asdf": 10,
    "zxcv": 9,
    "1234": 8,
    "password": 12,
    "letmein": 10,
    "admin": 9,
    "welcome": 8,
}

GRADE_THRESHOLDS = {
    "A": 78,
    "B": 63,
    "C": 48,
    "D": 33,
}


# ============================================================================
# Utility Functions
# ============================================================================


def normalize_leet(text: str) -> str:
    """
    Convert l33t speak (leetspeak) characters to normal text.

    Args:
        text: Input string with potential leetspeak characters

    Returns:
        String with all leetspeak characters replaced with normal letters

    Example:
        >>> normalize_leet('p4ssw0rd')
        'password'
    """
    return "".join(LEET_REPLACEMENTS.get(char, char) for char in text.lower())


def extract_tokens(text: str):
    """
    Extract alphabetic tokens from text using regex.

    Args:
        text: Input string to tokenize

    Returns:
        List of lowercase alphabetic tokens

    Example:
        >>> extract_tokens('Hello World 123')
        ['hello', 'world']
    """
    return re.findall(r"[a-z]+", text.lower())


def has_keyboard_pattern(password: str) -> bool:
    """
    Detect if a password contains common keyboard patterns.

    Checks for:
    - Common predefined keyboard patterns (qwerty, asdf, zxcv, etc.)
    - Sequential characters from keyboard rows (forward and backward)

    Args:
        password: Password string to check

    Returns:
        True if keyboard pattern is detected, False otherwise

    Example:
        >>> has_keyboard_pattern('qwerty123')
        True
        >>> has_keyboard_pattern('p4ssw0rd')
        False
    """
    lowered = password.lower()
    if any(pattern in lowered for pattern in COMMON_KEYBOARD_PATTERNS):
        return True

    for row in KEYBOARD_ROWS:
        for i in range(len(row) - 3):
            seq = row[i : i + 4]
            if seq in lowered or seq[::-1] in lowered:
                return True
    return False
