import argparse
import importlib
import re
from collections import Counter
from pathlib import Path

from shared_constants import (
    WORD_CATEGORIES,
    LEET_REPLACEMENTS,
    KEYBOARD_ROWS,
    COMMON_KEYBOARD_PATTERNS,
    normalize_leet,
    extract_tokens,
    has_keyboard_pattern,
)


TARGET_FOLDERS = [
    "DollarSymbol",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "Others",
]


def load_dictionary_words() -> set:
    try:
        english_words_module = importlib.import_module("english_words")
    except ModuleNotFoundError as exc:
        raise ImportError(
            "Missing dependency 'english-words'. Install it with `python3 -m pip install english-words`."
        ) from exc

    get_english_words_set = getattr(english_words_module, "get_english_words_set", None)
    if get_english_words_set is None:
        raise ImportError("Installed 'english-words' package is missing get_english_words_set().")

    return set(get_english_words_set(["web2"], lower=True, alpha=True))


DICTIONARY_WORDS = None


def get_dictionary_words() -> set:
    global DICTIONARY_WORDS
    if DICTIONARY_WORDS is None:
        DICTIONARY_WORDS = load_dictionary_words()
    return DICTIONARY_WORDS


def is_lfs_pointer(file_path: Path) -> bool:
    try:
        with file_path.open("r", encoding="utf-8", errors="replace") as handle:
            first_line = handle.readline().strip()
            return first_line == "version https://git-lfs.github.com/spec/v1"
    except OSError:
        return False


def iter_passwords(base_dir: Path):
    files_scanned = 0
    files_skipped_lfs = 0

    for folder in TARGET_FOLDERS:
        file_path = base_dir / folder / f"{folder}.txt"
        if not file_path.exists():
            print(f"[WARN] Missing file: {file_path}")
            continue

        files_scanned += 1
        if is_lfs_pointer(file_path):
            files_skipped_lfs += 1
            print(f"[WARN] Skipping Git LFS pointer file: {file_path}")
            continue

        with file_path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                password = raw_line.rstrip("\r\n")
                if password:
                    yield password

    print(f"\nFiles scanned: {files_scanned}")
    if files_skipped_lfs:
        print(f"Files skipped (Git LFS pointers): {files_skipped_lfs}")


def run_step4(base_dir: Path, top_n: int):
    total = 0
    dictionary_matches = 0
    keyboard_matches = 0
    leet_detected = 0

    matched_words = Counter()
    category_counts = Counter()
    pattern_type_counts = Counter()

    for password in iter_passwords(base_dir):
        total += 1
        lowered = password.lower()
        normalized = normalize_leet(password)

        tokens_plain = set(extract_tokens(lowered))
        tokens_leet = set(extract_tokens(normalized))

        plain_hits = tokens_plain.intersection(get_dictionary_words())
        leet_hits = tokens_leet.intersection(get_dictionary_words())

        if plain_hits:
            dictionary_matches += 1
            pattern_type_counts["dictionary_lookup"] += 1
            for word in plain_hits:
                matched_words[word] += 1

        # Count only words that appear after l33t normalization (not already plain hits).
        only_leet_hits = leet_hits.difference(plain_hits)
        if only_leet_hits:
            leet_detected += 1
            pattern_type_counts["l33t_detection"] += 1
            for word in only_leet_hits:
                matched_words[word] += 1

        if has_keyboard_pattern(password):
            keyboard_matches += 1
            pattern_type_counts["keyboard_pattern"] += 1

        combined_hits = plain_hits.union(leet_hits)
        for category, word_set in WORD_CATEGORIES.items():
            # Count categories at password-level (presence), not per-word frequency.
            if combined_hits.intersection(word_set):
                category_counts[category] += 1
                pattern_type_counts[f"word_category:{category}"] += 1

    print("\n=== STEP 4: SEMANTIC DECOMPOSITION (DollarSymbol -> Others) ===")
    print(f"Target folders: {', '.join(TARGET_FOLDERS)}")
    print(f"Total passwords processed: {total:,}")

    if total == 0:
        print("No passwords processed. If you expected data, run `git lfs pull` first.")
        return

    def pct(value: int) -> float:
        return (value / total) * 100.0

    print("\nDictionary lookup:")
    print(f"- Passwords with dictionary words: {dictionary_matches:,} ({pct(dictionary_matches):.2f}%)")

    print("\nWord classification (password-level counts):")
    for category, count in category_counts.most_common():
        print(f"- {category}: {count:,} ({pct(count):.2f}%)")

    print("\nL33t detection:")
    print(f"- Passwords with l33t-only recovered words: {leet_detected:,} ({pct(leet_detected):.2f}%)")

    print("\nKeyboard patterns:")
    print(f"- Passwords with keyboard patterns: {keyboard_matches:,} ({pct(keyboard_matches):.2f}%)")

    print(f"\nTop {top_n} matched dictionary words:")
    for word, count in matched_words.most_common(top_n):
        print(f"- {word}: {count:,}")

    print("\nPattern type ranking (most common first):")
    for label, count in pattern_type_counts.most_common():
        print(f"- {label}: {count:,}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Step 4 semantic decomposition for folders DollarSymbol through Others"
    )
    parser.add_argument(
        "--base-dir",
        default="data/archive",
        help="Base dataset directory containing archive subfolders (default: data/archive)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Top N words to print (default: 20)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_step4(Path(args.base_dir), args.top)


if __name__ == "__main__":
    main()
