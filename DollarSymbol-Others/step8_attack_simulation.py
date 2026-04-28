"""Step 8 attack simulation for dictionary and pattern-priority attacks."""

import argparse
import importlib
import json
import sys
import time
from pathlib import Path
from typing import Iterator

from shared_constants import (
    WORD_CATEGORIES,
    SPECIFIC_SEQUENCE_PATTERNS,
    LEET_REPLACEMENTS,
)


def load_english_words() -> set[str]:
    try:
        english_words_module = importlib.import_module("english_words")
    except ImportError:
        return set()

    get_english_words_set = getattr(english_words_module, "get_english_words_set", None)
    if get_english_words_set is None:
        return set()

    return set(get_english_words_set(["web2"], lower=True, alpha=True))


ENGLISH_WORDS = load_english_words()
ORDERED_ENGLISH_WORDS = tuple(sorted(ENGLISH_WORDS, key=lambda item: (len(item), item)))
PRIORITY_ORDER = ["names", "nouns", "verbs", "adjectives", "places", "dates"]


def build_priority_seed_words() -> list[str]:
    candidates = []

    for category in PRIORITY_ORDER:
        candidates.extend(sorted(WORD_CATEGORIES.get(category, [])))

    for category, words in WORD_CATEGORIES.items():
        if category not in PRIORITY_ORDER:
            candidates.extend(sorted(words))

    candidates.extend(SPECIFIC_SEQUENCE_PATTERNS.keys())

    common_passwords = [
        "password", "123456", "12345678", "qwerty", "abc123",
        "monkey", "1234567", "letmein", "trustno1", "dragon",
        "baseball", "iloveyou", "master", "sunshine", "ashley",
        "bailey", "passw0rd", "shadow", "123123", "654321",
        "superman", "qazwsx", "michael", "football", "welcome",
        "jesus", "ninja", "mustang", "password1", "123456789",
        "1234567890", "princess", "solo", "cookie", "flower",
        "starwars", "whatever", "cheese", "summer", "london",
        "jennifer", "harley", "ranger", "hello", "buster",
        "butterfly", "123qwe", "charlie", "aa123456", "donald",
        "martin", "peanut", "zaq1zaq1", "camaro", "chelsea",
        "1qaz2wsx", "blue", "diamond", "nascar", "jackson",
        "computer", "wizard", "maverick", "freedom", "pepper",
        "robert", "jordan", "samsung", "ferrari", "nicholas",
        "love", "maggie", "tigger", "hunter", "soccer",
        "killer", "fuckyou", "merlin", "matrix", "1q2w3e4r",
        "access", "blink182", "master", "jordan23", "q1w2e3r4",
        "killer", "jordan", "secret", "banana", "ranger",
        "jackson", "654321", "thomas", "qwerty123", "lovely",
        "phoenix", "admin", "azerty", "shadow", "1111",
    ]
    candidates.extend(common_passwords)

    seen = set()
    result = []
    for word in candidates:
        if word.lower() not in seen:
            seen.add(word.lower())
            result.append(word)

    return result


def iter_sorted_english_words() -> Iterator[str]:
    for word in ORDERED_ENGLISH_WORDS:
        yield word


def iter_dictionary_guesses() -> Iterator[str]:
    for word in build_priority_seed_words():
        for variant in generate_word_variations(word, LEET_REPLACEMENTS):
            yield variant

    for word in iter_sorted_english_words():
        yield word

    for word in iter_sorted_english_words():
        for variant in generate_word_variations(word, LEET_REPLACEMENTS):
            if variant != word:
                yield variant


def generate_word_variations(word: str, leet_map: dict) -> list[str]:
    """
    Generate all variations of a word for pattern-priority attack.

    Args:
        word: Base word to generate variations for
        leet_map: Dictionary mapping l33t characters to normal characters

    Returns:
        List of word variations in priority order
    """
    variations = [word]

    # Add single digits 0-9
    for d in range(10):
        variations.append(f"{word}{d}")

    # Add double digits 00-99
    for d in range(100):
        variations.append(f"{word}{d:02d}")

    # Add common three digit sequence
    variations.append(f"{word}123")

    # Add common years
    for year in [2020, 2021, 2022, 2023, 2024, 2025, 2026, 1990, 2000]:
        variations.append(f"{word}{year}")

    # Add common symbols
    for sym in ["!", "@", "#", "$"]:
        variations.append(f"{word}{sym}")

    # Capitalization variants
    variations.append(word.capitalize())
    variations.append(word.upper())

    # L33t variants (reverse: normal -> l33t)
    # Create reverse mapping
    reverse_leet = {}
    for leet_char, normal_char in leet_map.items():
        if normal_char not in reverse_leet:
            reverse_leet[normal_char] = []
        reverse_leet[normal_char].append(leet_char)

    leet_word = word.lower()
    for normal_char, leet_chars in reverse_leet.items():
        if normal_char in leet_word:
            leet_word = leet_word.replace(normal_char, leet_chars[0], 1)

    if leet_word != word and leet_word not in variations:
        variations.append(leet_word)

    return variations


def dictionary_attack(
    targets: list[str],
    max_attempts: int = 10000,
    speed: str = "fast"
) -> list[dict]:
    start_time = time.time()
    attempts = 0
    remaining: dict[str, list[str]] = {}
    for target in targets:
        remaining.setdefault(target.casefold(), []).append(target)
    cracked_at: dict[str, int] = {}
    cracked_with: dict[str, str] = {}
    cracked_elapsed: dict[str, float] = {}

    for candidate in iter_dictionary_guesses():
        if attempts >= max_attempts or not remaining:
            break

        attempts += 1

        if speed == "realistic":
            time.sleep(0.001)

        matched_targets = remaining.pop(candidate.casefold(), None)
        if matched_targets is not None:
            elapsed = round(time.time() - start_time, 3)
            for matched_target in matched_targets:
                cracked_at[matched_target] = attempts
                cracked_with[matched_target] = candidate
                cracked_elapsed[matched_target] = elapsed

    total_elapsed = round(time.time() - start_time, 3)
    results = []
    for target in targets:
        cracked = target in cracked_at
        results.append(
            {
                "target": target,
                "cracked": cracked,
                "attempts": cracked_at.get(target, attempts),
                "matched_with": cracked_with.get(target),
                "elapsed_time": cracked_elapsed.get(target, total_elapsed),
            }
        )

    return results


def pattern_priority_attack(
    target: str,
    max_attempts: int = 10000,
    speed: str = "fast",
    verbose: bool = False
) -> dict:
    """
    Attempt to crack a password using pattern-priority attack.

    This attack tries word categories in ranked order based on Phase 1 findings:
    1. Names (highest priority)
    2. Nouns
    3. Verbs
    4. Adjectives
    5. Places
    6. Dates

    For each category, generates variations (digits, years, symbols, l33t).

    Args:
        target: Password to crack
        max_attempts: Maximum attempts before giving up
        speed: "fast" (instant compare) or "realistic" (add delay)
        verbose: If True, print which category is being tried

    Returns:
        dict with {target, cracked, attempts, elapsed_time, cracked_by_pattern_type, matched_with}
    """
    start_time = time.time()
    attempts = 0

    # Priority order based on Phase 1 rankings
    priority_order = ["names", "nouns", "verbs", "adjectives", "places", "dates"]

    for category in priority_order:
        if verbose:
            print(f"[INFO] Trying category: {category}")

        words = WORD_CATEGORIES.get(category, [])

        for word in words:
            # Generate all variations for this word
            variations = generate_word_variations(word, LEET_REPLACEMENTS)

            for variant in variations:
                if attempts >= max_attempts:
                    elapsed = time.time() - start_time
                    return {
                        "target": target,
                        "cracked": False,
                        "attempts": attempts,
                        "matched_with": None,
                        "elapsed_time": round(elapsed, 3),
                        "cracked_by_pattern_type": None,
                    }

                attempts += 1

                # Speed simulation
                if speed == "realistic":
                    time.sleep(0.001)  # 1ms delay per attempt

                # Check match (case-insensitive and exact match)
                if variant.lower() == target.lower() or variant == target:
                    elapsed = time.time() - start_time
                    return {
                        "target": target,
                        "cracked": True,
                        "attempts": attempts,
                        "matched_with": variant,
                        "elapsed_time": round(elapsed, 3),
                        "cracked_by_pattern_type": category,
                    }

    # No match found after all categories
    elapsed = time.time() - start_time
    return {
        "target": target,
        "cracked": False,
        "attempts": attempts,
        "matched_with": None,
        "elapsed_time": round(elapsed, 3),
        "cracked_by_pattern_type": None,
    }


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Step 8 attack simulation: dictionary and pattern-priority attacks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dictionary attack on single password
  %(prog)s --mode dictionary --target "password123"

  # Pattern-priority attack with verbose output
  %(prog)s --mode pattern-priority --target "john123" --verbose

  # Attack with JSON output
  %(prog)s --mode pattern-priority --target "dragon" --json-output results.json

  # Attack from file with limit
  %(prog)s --mode pattern-priority --target-file passwords.txt --max-attempts 5000
"""
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=["dictionary", "pattern-priority"],
        help="Attack mode"
    )
    parser.add_argument(
        "--target",
        help="Single password to attack"
    )
    parser.add_argument(
        "--target-file",
        help="File with passwords to attack (one per line)"
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=10000,
        help="Maximum guesses from the attack stream (default: 10000)"
    )
    parser.add_argument(
        "--speed",
        choices=["fast", "realistic"],
        default="fast",
        help="Attack speed: 'fast' (instant) or 'realistic' (with delay)"
    )
    parser.add_argument(
        "--json-output",
        help="Path for JSON output file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress (pattern-priority mode only)"
    )

    return parser.parse_args()


def main():
    """Main entry point for attack simulation."""
    args = parse_args()

    # Validate: need either --target or --target-file
    if not args.target and not args.target_file:
        print("[ERROR] Either --target or --target-file is required", file=sys.stderr)
        sys.exit(1)

    # Get targets
    targets = []
    if args.target:
        targets.append(args.target)
    if args.target_file:
        target_path = Path(args.target_file)
        if not target_path.exists():
            print(f"[ERROR] Target file not found: {target_path}", file=sys.stderr)
            sys.exit(1)
        with target_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                pw = line.rstrip("\r\n")
                if pw:
                    targets.append(pw)

    if not targets:
        print("[ERROR] No non-empty targets were provided", file=sys.stderr)
        sys.exit(1)

    if args.mode == "dictionary":
        priority_seed_count = len(build_priority_seed_words())
        print("[INFO] Preparing streamed attack dictionary...")
        print(f"[INFO] Priority seed words: {priority_seed_count}")
        print(f"[INFO] english-words entries: {len(ENGLISH_WORDS)}")
        if ENGLISH_WORDS:
            print("[INFO] Dictionary mode streams priority seeds first, then raw english-words entries")
        else:
            print("[WARN] english-words not available; dictionary mode will use project seed words only")

    # Run attacks
    results = []
    if args.mode == "dictionary":
        results = dictionary_attack(targets, args.max_attempts, args.speed)

        for result in results:
            status = "CRACKED" if result["cracked"] else "FAILED"
            matched_info = f" (matched: {result['matched_with']})" if result["cracked"] else ""
            print(
                f"[{status}] {result['target']}: {result['attempts']} attempts "
                f"({result['elapsed_time']}s){matched_info}"
            )

    else:
        for target in targets:
            result = pattern_priority_attack(target, args.max_attempts, args.speed, args.verbose)
            results.append(result)

            # Print progress
            status = "CRACKED" if result["cracked"] else "FAILED"
            matched_info = f" (matched: {result['matched_with']})" if result["cracked"] else ""
            pattern_info = f" [pattern: {result['cracked_by_pattern_type']}]" if result["cracked"] else ""
            print(f"[{status}] {target}: {result['attempts']} attempts ({result['elapsed_time']}s){matched_info}{pattern_info}")

    # Summary
    cracked_count = sum(1 for r in results if r["cracked"])
    print(f"\n=== ATTACK SUMMARY ===")
    print(f"Total targets: {len(results)}")
    print(f"Cracked: {cracked_count} ({100*cracked_count/len(results):.1f}%)")
    print(f"Failed: {len(results) - cracked_count}")

    # JSON output
    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "mode": args.mode,
            "max_attempts": args.max_attempts,
            "speed": args.speed,
            "results": results,
            "summary": {
                "total": len(results),
                "cracked": cracked_count,
                "failed": len(results) - cracked_count,
            }
        }

        if args.mode == "dictionary":
            output_data["priority_seed_count"] = len(build_priority_seed_words())
            output_data["english_word_count"] = len(ENGLISH_WORDS)
            output_data["dictionary_streamed"] = True

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"Results written to: {output_path}")


if __name__ == "__main__":
    main()
