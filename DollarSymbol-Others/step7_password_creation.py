#!/usr/bin/env python3
"""Step 7 password creation for hardening or combining passwords."""

import argparse
import json
import math
import random
import re
import string
import sys
from pathlib import Path

from shared_constants import (
    LEET_REPLACEMENTS,
    WORD_CATEGORIES,
    GRADE_THRESHOLDS,
    normalize_leet,
    extract_tokens,
)
from step6_password_grading import (
    grade_password,
    detect_pattern_types,
    load_dictionary_words,
    parse_model,
)


def reverse_leet_speak(password: str) -> str:
    """
    Convert l33t speak characters to normal text to avoid l33t_detection penalty.

    Args:
        password: Password potentially containing l33t speak

    Returns:
        Password with l33t speak normalized

    Example:
        >>> reverse_leet_speak('p4ssw0rd')
        'password'
    """
    return normalize_leet(password)


def add_case_mixing(password: str) -> str:
    """
    Add case mixing to password for complexity bonus.
    Capitalizes first letter and some random positions.

    Args:
        password: Input password

    Returns:
        Password with mixed case

    Example:
        >>> add_case_mixing('password')
        'Password' or 'PasSword'
    """
    if not password:
        return password

    chars = list(password)

    # Capitalize first letter if alphabetic
    if chars[0].isalpha():
        chars[0] = chars[0].upper()

    # Randomly capitalize 20-30% of other alphabetic characters
    for i in range(1, len(chars)):
        if chars[i].isalpha() and random.random() < 0.25:
            chars[i] = chars[i].upper()

    return ''.join(chars)


def insert_separators(password: str) -> str:
    """
    Insert separators between detected segments (words/digits).
    Avoids weak separators like '!' at end or '123' suffix.

    Args:
        password: Input password

    Returns:
        Password with separators inserted

    Example:
        >>> insert_separators('password123')
        'password-123'
    """
    # Use good separators (avoid ! which has specific penalty at end)
    separators = ['-', '_', '.', '#']

    # Detect boundaries between letters and digits
    result = []
    prev_type = None

    for char in password:
        current_type = 'letter' if char.isalpha() else 'digit' if char.isdigit() else 'other'

        # Insert separator at letter<->digit boundary
        if prev_type and prev_type != current_type and current_type != 'other' and prev_type != 'other':
            result.append(random.choice(separators))

        result.append(char)
        prev_type = current_type

    return ''.join(result)


def extend_length(password: str, min_length: int) -> str:
    """
    Extend password to meet minimum length requirement.
    Appends random characters (letters, digits, symbols).

    Args:
        password: Input password
        min_length: Minimum required length

    Returns:
        Password extended to at least min_length

    Example:
        >>> extend_length('pass', 8)
        'pass7K#@'
    """
    if len(password) >= min_length:
        return password

    needed = min_length - len(password)
    extension_chars = string.ascii_letters + string.digits + "!@#$%^&*"

    # Append random characters
    extension = ''.join(random.choice(extension_chars) for _ in range(needed))
    return password + extension


def insert_symbols(password: str) -> str:
    """
    Insert symbols at strategic positions (not at end to avoid specific penalty).

    Args:
        password: Input password

    Returns:
        Password with symbols inserted

    Example:
        >>> insert_symbols('password')
        'p@ssword' or 'pa$sword'
    """
    if len(password) < 3:
        return password

    symbols = ['@', '#', '$', '%', '^', '&', '*']

    # Insert 1-2 symbols at random positions (not at end)
    chars = list(password)
    num_symbols = min(2, len(password) // 4)  # Max 2 symbols, 1 per 4 chars

    # Get valid positions (not at end, not first char)
    valid_positions = list(range(1, len(chars) - 1)) if len(chars) > 2 else []

    if not valid_positions:
        return password

    # Randomly select positions
    insert_positions = random.sample(valid_positions, min(num_symbols, len(valid_positions)))

    for pos in sorted(insert_positions, reverse=True):
        chars[pos] = random.choice(symbols)

    return ''.join(chars)


def combine_elements(
    elements: list[str],
    model: dict,
    dictionary_words: set,
    alpha: float,
    min_length: int = 8,
    target_grade: str = "B",
    separator: str = "auto"
) -> dict:
    """
    Combine user-provided elements into a strong password.

    Strategy:
    1. Check each element against WORD_CATEGORIES - if weak, transform it
    2. Apply case mixing to elements
    3. Join with secure separator
    4. Add symbols/chars if needed for length
    5. Verify grade meets target

    Args:
        elements: List of words/elements to combine
        model: Step 5 n-gram model
        dictionary_words: Dictionary for pattern detection
        alpha: Laplace smoothing
        min_length: Minimum password length
        target_grade: Target grade (A/B/C/D)
        separator: Separator to use or "auto"

    Returns:
        dict with combined password and metadata
    """
    SAFE_SEPARATORS = ["-", "_", "#", "."]

    # Store original elements
    original_elements = elements.copy()
    transformations_log = []

    # Get all weak words from WORD_CATEGORIES
    weak_words = set()
    for category, words in WORD_CATEGORIES.items():
        weak_words.update(words)

    # Transform weak elements
    transformed_elements = []
    for element in elements:
        element_lower = element.lower()

        # Check if element is weak
        if element_lower in weak_words:
            # Apply transformation: capitalize + optional symbol insertion
            transformed = element.capitalize()

            # Insert symbol in middle for extra strength
            if len(transformed) >= 3 and random.random() < 0.6:
                mid_pos = len(transformed) // 2
                symbol = random.choice(['@', '#', '$', '%'])
                transformed = transformed[:mid_pos] + symbol + transformed[mid_pos:]
                transformations_log.append(f"'{element}' -> '{transformed}' (weak word + symbol)")
            else:
                transformations_log.append(f"'{element}' -> '{transformed}' (weak word capitalized)")

            transformed_elements.append(transformed)
        else:
            # Apply case mixing to non-weak elements
            mixed = add_case_mixing(element)
            transformed_elements.append(mixed)
            if mixed != element:
                transformations_log.append(f"'{element}' -> '{mixed}' (case mixing)")
            else:
                transformations_log.append(f"'{element}' unchanged")

    # Choose separator
    if separator == "auto":
        separator_used = random.choice(SAFE_SEPARATORS)
    else:
        separator_used = separator

    # Join elements with separator
    combined = separator_used.join(transformed_elements)

    # Extend if needed for minimum length
    if len(combined) < min_length:
        combined = extend_length(combined, min_length)
        transformations_log.append(f"Extended to meet min_length {min_length}")

    # Grade the combined password
    target_score = GRADE_THRESHOLDS.get(target_grade, 63)
    result = grade_password(combined, model, dictionary_words, alpha)
    current_score = result["final_score"]
    current_grade = result["letter_grade"]

    # If grade is below target, add more transformations
    max_iterations = 3
    iteration = 0
    while current_score < target_score and iteration < max_iterations:
        # Try inserting symbols
        combined = insert_symbols(combined)
        transformations_log.append(f"Iteration {iteration+1}: Added symbols for better grade")

        # Re-grade
        result = grade_password(combined, model, dictionary_words, alpha)
        current_score = result["final_score"]
        current_grade = result["letter_grade"]
        iteration += 1

    return {
        "input_elements": original_elements,
        "transformed_elements": transformed_elements,
        "combined": combined,
        "separator": separator_used,
        "grade": current_grade,
        "score": current_score,
        "transformations_applied": transformations_log,
    }


def harden_password(
    original: str,
    model: dict,
    dictionary_words: set,
    alpha: float,
    min_length: int,
    target_grade: str
) -> dict:
    """
    Harden a weak password through iterative transformations.

    Applies transformations in order:
    1. Reverse l33t speak if detected
    2. Add case mixing
    3. Insert separators between segments
    4. Extend if too short
    5. Insert symbols for bonus

    Stops when target grade is reached or all transformations applied.

    Args:
        original: Original password to harden
        model: Character n-gram model from Step 5
        dictionary_words: Set of dictionary words for pattern detection
        alpha: Laplace smoothing parameter
        min_length: Minimum password length
        target_grade: Target grade letter (A/B/C/D)

    Returns:
        Dictionary containing:
        - original: Original password
        - hardened: Hardened password
        - original_grade: Original letter grade
        - original_score: Original numeric score
        - hardened_grade: Hardened letter grade
        - hardened_score: Hardened numeric score
        - improvement: Score improvement
        - transformations: List of transformations applied
    """
    # Grade original password
    original_result = grade_password(original, model, dictionary_words, alpha)
    original_score = original_result["final_score"]
    original_grade = original_result["letter_grade"]

    # Detect weaknesses
    pattern_types = detect_pattern_types(original, dictionary_words)

    # Target score threshold
    target_score = GRADE_THRESHOLDS.get(target_grade, 63)

    # Apply transformations iteratively
    current_password = original
    transformations_applied = []
    current_score = original_score
    current_grade = original_grade

    # Transformation 1: Reverse l33t speak if detected
    if any('l33t' in label for label in pattern_types.get('labels', [])):
        transformed = reverse_leet_speak(current_password)
        if transformed != current_password:
            current_password = transformed
            transformations_applied.append('reverse_leet')
            # Grade after transformation
            result = grade_password(current_password, model, dictionary_words, alpha)
            current_score = result["final_score"]
            current_grade = result["letter_grade"]

            if current_score >= target_score:
                return {
                    "original": original,
                    "hardened": current_password,
                    "original_grade": original_grade,
                    "original_score": original_score,
                    "hardened_grade": current_grade,
                    "hardened_score": current_score,
                    "improvement": current_score - original_score,
                    "transformations": transformations_applied,
                }

    # Transformation 2: Add case mixing
    transformed = add_case_mixing(current_password)
    if transformed != current_password:
        current_password = transformed
        transformations_applied.append('case_mixing')
        result = grade_password(current_password, model, dictionary_words, alpha)
        current_score = result["final_score"]
        current_grade = result["letter_grade"]

        if current_score >= target_score:
            return {
                "original": original,
                "hardened": current_password,
                "original_grade": original_grade,
                "original_score": original_score,
                "hardened_grade": current_grade,
                "hardened_score": current_score,
                "improvement": current_score - original_score,
                "transformations": transformations_applied,
            }

    # Transformation 3: Insert separators
    # Only if password has letter-digit boundaries
    if any(c.isdigit() for c in current_password) and any(c.isalpha() for c in current_password):
        transformed = insert_separators(current_password)
        if transformed != current_password:
            current_password = transformed
            transformations_applied.append('separator_insertion')
            result = grade_password(current_password, model, dictionary_words, alpha)
            current_score = result["final_score"]
            current_grade = result["letter_grade"]

            if current_score >= target_score:
                return {
                    "original": original,
                    "hardened": current_password,
                    "original_grade": original_grade,
                    "original_score": original_score,
                    "hardened_grade": current_grade,
                    "hardened_score": current_score,
                    "improvement": current_score - original_score,
                    "transformations": transformations_applied,
                }

    # Transformation 4: Extend if too short
    if len(current_password) < min_length:
        transformed = extend_length(current_password, min_length)
        if transformed != current_password:
            current_password = transformed
            transformations_applied.append('length_extension')
            result = grade_password(current_password, model, dictionary_words, alpha)
            current_score = result["final_score"]
            current_grade = result["letter_grade"]

            if current_score >= target_score:
                return {
                    "original": original,
                    "hardened": current_password,
                    "original_grade": original_grade,
                    "original_score": original_score,
                    "hardened_grade": current_grade,
                    "hardened_score": current_score,
                    "improvement": current_score - original_score,
                    "transformations": transformations_applied,
                }

    # Transformation 5: Insert symbols
    transformed = insert_symbols(current_password)
    if transformed != current_password:
        current_password = transformed
        transformations_applied.append('symbol_insertion')
        result = grade_password(current_password, model, dictionary_words, alpha)
        current_score = result["final_score"]
        current_grade = result["letter_grade"]

    # Ensure we don't return a password worse than the original
    if current_score < original_score:
        return {
            "original": original,
            "hardened": original,
            "original_grade": original_grade,
            "original_score": original_score,
            "hardened_grade": original_grade,
            "hardened_score": original_score,
            "improvement": 0,
            "transformations": [],
            "note": "Transformations would have decreased score; original retained"
        }

    # Return final result
    return {
        "original": original,
        "hardened": current_password,
        "original_grade": original_grade,
        "original_score": original_score,
        "hardened_grade": current_grade,
        "hardened_score": current_score,
        "improvement": current_score - original_score,
        "transformations": transformations_applied,
    }


def main():
    """Main entry point for password creation script."""
    parser = argparse.ArgumentParser(
        description="Step 7 password creation: hardening and combining modes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Harden a weak password
  %(prog)s --mode harden --password "password" --model models/character_ngram_model.json

  # Harden with custom target grade and length
  %(prog)s --mode harden --password "dragon123" --model models/character_ngram_model.json --target-grade A --min-length 12

  # Combine elements into a strong password
  %(prog)s --mode combine --elements "dragon,2024,secure" --model models/character_ngram_model.json

  # Combine with custom separator
  %(prog)s --mode combine --elements "hello,world" --model models/character_ngram_model.json --separator "-"
"""
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=["harden", "combine"],
        help="Password creation mode: 'harden' to strengthen weak passwords, 'combine' to merge elements"
    )
    parser.add_argument(
        "--password",
        help="Password to harden (required for harden mode)"
    )
    parser.add_argument(
        "--elements",
        help="Comma-separated elements to combine (required for combine mode)"
    )
    parser.add_argument(
        "--separator",
        default="auto",
        help="Separator between elements: 'auto' (default), '-', '_', '.', or '#'"
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Path to Step 5 character n-gram model JSON"
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=8,
        help="Minimum password length (default: 8)"
    )
    parser.add_argument(
        "--target-grade",
        default="B",
        choices=["A", "B", "C", "D"],
        help="Target grade letter (default: B)"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Laplace smoothing parameter (default: 0.5)"
    )

    args = parser.parse_args()

    # Validate mode-specific arguments
    if args.mode == "harden" and not args.password:
        print("[ERROR] --password is required for harden mode", file=sys.stderr)
        sys.exit(1)

    if args.mode == "combine" and not args.elements:
        print("[ERROR] --elements is required for combine mode", file=sys.stderr)
        sys.exit(1)

    # Load model
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"[ERROR] Model file not found: {model_path}", file=sys.stderr)
        sys.exit(1)

    try:
        model = parse_model(model_path)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in model file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}", file=sys.stderr)
        sys.exit(1)

    # Load dictionary
    dictionary_words = load_dictionary_words()

    if args.mode == "harden":
        # Harden password
        result = harden_password(
            args.password,
            model,
            dictionary_words,
            args.alpha,
            args.min_length,
            args.target_grade
        )

        # Print result
        print("\n" + "="*60)
        print("PASSWORD HARDENING RESULT")
        print("="*60)
        print(f"Original password:     {result['original']}")
        print(f"Original grade:        {result['original_grade']} ({result['original_score']}/100)")
        print(f"\nHardened password:     {result['hardened']}")
        print(f"Hardened grade:        {result['hardened_grade']} ({result['hardened_score']}/100)")
        print(f"\nImprovement:           +{result['improvement']:.1f} points")
        print(f"Transformations:       {', '.join(result['transformations']) if result['transformations'] else 'none needed'}")
        print("="*60 + "\n")

    elif args.mode == "combine":
        # Parse elements
        elements = [e.strip() for e in args.elements.split(",") if e.strip()]

        if len(elements) == 0:
            print("[ERROR] No valid elements provided", file=sys.stderr)
            sys.exit(1)

        if len(elements) > 5:
            print("[ERROR] Maximum 5 elements allowed", file=sys.stderr)
            sys.exit(1)

        # Combine elements
        result = combine_elements(
            elements,
            model,
            dictionary_words,
            args.alpha,
            args.min_length,
            args.target_grade,
            args.separator
        )

        # Print result
        print("\n" + "="*60)
        print("PASSWORD COMBINING RESULT")
        print("="*60)
        print(f"Input elements:        {', '.join(result['input_elements'])}")
        print(f"Transformed elements:  {', '.join(result['transformed_elements'])}")
        print(f"Combined password:     {result['combined']}")
        print(f"Grade:                 {result['grade']} ({result['score']}/100)")
        print(f"Separator used:        '{result['separator']}'")
        print(f"\nTransformations applied:")
        for t in result['transformations_applied']:
            print(f"  - {t}")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()
