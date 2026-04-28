import argparse
import importlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from shared_constants import (
    LEET_REPLACEMENTS,
    WORD_CATEGORIES,
    KEYBOARD_ROWS,
    COMMON_KEYBOARD_PATTERNS,
    PATTERN_TYPE_PENALTIES,
    SPECIFIC_SEQUENCE_PATTERNS,
    GRADE_THRESHOLDS,
    normalize_leet,
    extract_tokens,
    has_keyboard_pattern,
)


START_TOKEN = "<s>"
END_TOKEN = "</s>"

BASE_Z_CENTER = 35.0
BASE_Z_SCALE = 11.0

BASE_WEIGHT = 1.00
PATTERN_PENALTY_WEIGHT = 0.90
SPECIFIC_PENALTY_WEIGHT = 0.85
BONUS_WEIGHT = 0.70
SCORE_OFFSET = 0.0

MAX_PRINT_REPORTS = 20


def load_dictionary_words() -> set:
    fallback_words = set().union(*WORD_CATEGORIES.values())
    fallback_words.update(SPECIFIC_SEQUENCE_PATTERNS.keys())

    try:
        english_words_module = importlib.import_module("english_words")
    except ModuleNotFoundError:
        print("[WARN] Missing dependency 'english-words'; using built-in fallback dictionary.")
        return fallback_words

    get_english_words_set = getattr(english_words_module, "get_english_words_set", None)
    if get_english_words_set is None:
        print("[WARN] Installed 'english-words' package missing get_english_words_set(); using fallback dictionary.")
        return fallback_words

    words = set(get_english_words_set(["web2"], lower=True, alpha=True))
    words.update(fallback_words)
    return words


def parse_model(model_path: Path) -> dict:
    with model_path.open("r", encoding="utf-8") as handle:
        model = json.load(handle)

    bigram_lookup = {item["context"]: item["next_counts"] for item in model["bigram_counts"]}
    trigram_lookup = {
        (item["context"][0], item["context"][1]): item["next_counts"] for item in model["trigram_counts"]
    }

    return {
        "metadata": model["metadata"],
        "tokens": model.get("tokens", {"start": START_TOKEN, "end": END_TOKEN}),
        "vocabulary": model["vocabulary"],
        "unigram_counts": model["unigram_counts"],
        "bigram_lookup": bigram_lookup,
        "trigram_lookup": trigram_lookup,
    }


def smoothed_probability(next_counts: dict, token: str, alpha: float, vocab_size: int) -> float:
    total = sum(next_counts.values())
    count = next_counts.get(token, 0)
    return (count + alpha) / (total + alpha * vocab_size)


def transition_probability(model: dict, prev2: str, prev1: str, nxt: str, alpha: float) -> float:
    vocabulary = model["vocabulary"]
    vocab_size = len(vocabulary)

    p_uni = smoothed_probability(model["unigram_counts"], nxt, alpha, vocab_size)
    p_bi = smoothed_probability(model["bigram_lookup"].get(prev1, {}), nxt, alpha, vocab_size)
    p_tri = smoothed_probability(model["trigram_lookup"].get((prev2, prev1), {}), nxt, alpha, vocab_size)

    return 0.60 * p_tri + 0.30 * p_bi + 0.10 * p_uni


def base_score_from_surprisal(average_surprisal: float, model: dict) -> float:
    stats = model["metadata"].get("surprisal_stats", {})
    std = stats.get("std", 0.0)
    mean = stats.get("mean", 0.0)
    if std and std > 0:
        z_score = (average_surprisal - mean) / std
        return max(0.0, min(70.0, BASE_Z_CENTER + BASE_Z_SCALE * z_score))
    return max(0.0, min(70.0, ((average_surprisal - 2.0) / 5.0) * 70.0))


def predictability_score(password: str, model: dict, alpha: float) -> dict:
    start_token = model["tokens"]["start"]
    end_token = model["tokens"]["end"]
    sequence = [start_token, start_token, *list(password), end_token]
    surprisal_sum = 0.0
    transition_count = 0

    for idx in range(2, len(sequence)):
        prev2 = sequence[idx - 2]
        prev1 = sequence[idx - 1]
        nxt = sequence[idx]
        probability = transition_probability(model, prev2, prev1, nxt, alpha)
        surprisal_sum += -math.log2(probability)
        transition_count += 1

    average_surprisal = surprisal_sum / max(transition_count, 1)
    base_score = base_score_from_surprisal(average_surprisal, model)

    return {
        "average_surprisal": average_surprisal,
        "base_score": base_score,
    }


def detect_pattern_types(password: str, dictionary_words: set) -> dict:
    lowered = password.lower()
    normalized = normalize_leet(password)
    category_vocabulary = set().union(*WORD_CATEGORIES.values())

    tokens_plain = set(extract_tokens(lowered))
    tokens_leet = set(extract_tokens(normalized))

    explicit_plain_hits = {word for word in category_vocabulary if word in lowered}
    explicit_leet_hits = {word for word in category_vocabulary if word in normalized and word not in lowered}

    plain_hits = tokens_plain.intersection(dictionary_words)
    leet_hits = tokens_leet.intersection(dictionary_words)
    plain_hits.update(explicit_plain_hits)
    leet_hits.update(explicit_leet_hits)

    only_leet_hits = leet_hits.difference(plain_hits)
    combined_hits = tokens_plain.union(tokens_leet).union(explicit_plain_hits).union(explicit_leet_hits)

    labels = set()
    matched_words = set()

    if plain_hits:
        labels.add("dictionary_lookup")
        matched_words.update(plain_hits)

    if only_leet_hits:
        labels.add("l33t_detection")
        matched_words.update(only_leet_hits)

    if has_keyboard_pattern(password):
        labels.add("keyboard_pattern")

    for category, words in WORD_CATEGORIES.items():
        if combined_hits.intersection(words):
            labels.add(f"word_category:{category}")

    penalty_breakdown = []
    for label in sorted(labels):
        points = PATTERN_TYPE_PENALTIES.get(label, 0)
        if points > 0:
            penalty_breakdown.append((label, points))

    return {
        "labels": sorted(labels),
        "matched_words": sorted(matched_words),
        "penalty_breakdown": penalty_breakdown,
        "total_penalty": min(sum(points for _, points in penalty_breakdown), 45),
    }


def detect_specific_penalties(password: str) -> dict:
    lowered = password.lower()
    matches = []

    for pattern, points in SPECIFIC_SEQUENCE_PATTERNS.items():
        if pattern in lowered:
            matches.append((f"contains:{pattern}", points))

    if lowered.endswith("!"):
        matches.append(("suffix:!", 6))
    if lowered.endswith("1"):
        matches.append(("suffix:1", 5))
    if lowered.endswith("123"):
        matches.append(("suffix:123", 8))
    if re.search(r"(.)\1{2,}", password):
        matches.append(("repetition:triple_char", 6))
    if re.search(r"(19|20)\d{2}$", lowered):
        matches.append(("suffix:year", 5))

    total = min(sum(points for _, points in matches), 30)
    return {
        "matches": matches,
        "total_penalty": total,
    }


def complexity_bonus(password: str) -> dict:
    length = len(password)

    if length >= 16:
        length_bonus = 18
    elif length >= 12:
        length_bonus = 14
    elif length >= 10:
        length_bonus = 10
    elif length >= 8:
        length_bonus = 6
    elif length >= 6:
        length_bonus = 2
    else:
        length_bonus = 0

    classes = 0
    classes += any(ch.islower() for ch in password)
    classes += any(ch.isupper() for ch in password)
    classes += any(ch.isdigit() for ch in password)
    classes += any(not ch.isalnum() for ch in password)
    class_bonus = {0: 0, 1: 0, 2: 4, 3: 8, 4: 12}[classes]

    unique_ratio = len(set(password)) / max(length, 1)
    if unique_ratio >= 0.8:
        uniqueness_bonus = 8
    elif unique_ratio >= 0.6:
        uniqueness_bonus = 5
    elif unique_ratio >= 0.4:
        uniqueness_bonus = 2
    else:
        uniqueness_bonus = 0

    total = min(length_bonus + class_bonus + uniqueness_bonus, 30)
    return {
        "length_bonus": length_bonus,
        "class_bonus": class_bonus,
        "uniqueness_bonus": uniqueness_bonus,
        "total_bonus": total,
    }


def score_to_grade(score: int) -> str:
    if score >= GRADE_THRESHOLDS["A"]:
        return "A"
    if score >= GRADE_THRESHOLDS["B"]:
        return "B"
    if score >= GRADE_THRESHOLDS["C"]:
        return "C"
    if score >= GRADE_THRESHOLDS["D"]:
        return "D"
    return "F"


def grade_password(password: str, model: dict, dictionary_words: set, alpha: float) -> dict:
    predictability = predictability_score(password, model, alpha)
    pattern_types = detect_pattern_types(password, dictionary_words)
    specific = detect_specific_penalties(password)
    bonus = complexity_bonus(password)

    weighted_base = predictability["base_score"] * BASE_WEIGHT
    weighted_pattern_penalty = pattern_types["total_penalty"] * PATTERN_PENALTY_WEIGHT
    weighted_specific_penalty = specific["total_penalty"] * SPECIFIC_PENALTY_WEIGHT
    weighted_bonus = bonus["total_bonus"] * BONUS_WEIGHT

    raw_score = (
        weighted_base
        - weighted_pattern_penalty
        - weighted_specific_penalty
        + weighted_bonus
        + SCORE_OFFSET
    )
    final_score = max(0, min(100, int(round(raw_score))))

    return {
        "password": password,
        "average_surprisal": predictability["average_surprisal"],
        "base_predictability_score": round(predictability["base_score"], 2),
        "weighted_components": {
            "base": round(weighted_base, 2),
            "pattern_penalty": round(weighted_pattern_penalty, 2),
            "specific_penalty": round(weighted_specific_penalty, 2),
            "bonus": round(weighted_bonus, 2),
        },
        "raw_score": round(raw_score, 2),
        "pattern_type_penalties": pattern_types,
        "specific_pattern_penalties": specific,
        "complexity_bonus": bonus,
        "final_score": final_score,
        "letter_grade": score_to_grade(final_score),
    }


def read_passwords_from_file(file_path: Path) -> list:
    passwords = []
    with file_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            password = raw_line.rstrip("\r\n")
            if password:
                passwords.append(password)
    return passwords


def print_grade_report(result: dict):
    print("\n---")
    print(f"Password: {result['password']}")
    print(f"Final score: {result['final_score']} ({result['letter_grade']})")
    print(f"Base predictability score: {result['base_predictability_score']:.2f}")
    print(f"Average surprisal (bits/char): {result['average_surprisal']:.3f}")

    print("Pattern type penalties:")
    if result["pattern_type_penalties"]["penalty_breakdown"]:
        for label, points in result["pattern_type_penalties"]["penalty_breakdown"]:
            print(f"- {label}: -{points}")
    else:
        print("- none")

    print("Specific pattern penalties:")
    if result["specific_pattern_penalties"]["matches"]:
        for label, points in result["specific_pattern_penalties"]["matches"]:
            print(f"- {label}: -{points}")
    else:
        print("- none")

    print("Complexity bonuses:")
    bonus = result["complexity_bonus"]
    print(f"- length_bonus: +{bonus['length_bonus']}")
    print(f"- class_bonus: +{bonus['class_bonus']}")
    print(f"- uniqueness_bonus: +{bonus['uniqueness_bonus']}")


def aggregate_stats(results: list) -> dict:
    grade_counts = defaultdict(int)
    for item in results:
        grade_counts[item["letter_grade"]] += 1

    mean_score = sum(item["final_score"] for item in results) / max(len(results), 1)
    return {
        "total_passwords": len(results),
        "mean_score": mean_score,
        "grade_distribution": dict(sorted(grade_counts.items())),
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Step 6 password grading using probabilistic predictability + pattern penalties"
    )
    parser.add_argument(
        "--model",
        default="DollarSymbol-Others/models/character_ngram_model.json",
        help="Path to Step 5 model JSON",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Single password to grade",
    )
    parser.add_argument(
        "--input-file",
        default=None,
        help="File with one password per line for batch grading",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Laplace smoothing constant (default: 0.5)",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional path to save detailed grading JSON",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}. Run step5_probabilistic_prediction.py first."
        )

    model = parse_model(model_path)
    dictionary_words = load_dictionary_words()

    passwords = []
    if args.password is not None:
        passwords.append(args.password)
    if args.input_file is not None:
        passwords.extend(read_passwords_from_file(Path(args.input_file)))

    if not passwords:
        entered = input("Enter password to grade: ").strip()
        if entered:
            passwords.append(entered)

    if not passwords:
        print("No passwords provided.")
        return

    print("\n=== STEP 6: PASSWORD GRADING ===")
    print(f"Model passwords trained on: {model['metadata']['total_passwords']:,}")
    print("Scoring mode: natural_raw")

    alpha_used = args.alpha
    stats_alpha = model["metadata"].get("surprisal_stats", {}).get("alpha")
    if stats_alpha is not None and abs(stats_alpha - args.alpha) > 1e-12:
        print(
            f"[WARN] Provided alpha ({args.alpha}) differs from Step 5 surprisal_stats alpha ({stats_alpha}); "
            f"using {stats_alpha} for consistency."
        )
        alpha_used = stats_alpha
    print(f"Alpha used: {alpha_used}")

    if "surprisal_stats" not in model["metadata"]:
        print("[WARN] Model metadata has no surprisal_stats; base mapping will fall back to legacy linear mode.")

    results = [grade_password(password, model, dictionary_words, alpha_used) for password in passwords]

    reports_to_print = min(MAX_PRINT_REPORTS, len(results))
    for result in results[:reports_to_print]:
        print_grade_report(result)
    if reports_to_print < len(results):
        print(f"\n[INFO] Printed {reports_to_print} detailed reports out of {len(results)} passwords.")

    stats = aggregate_stats(results)
    print("\n=== BATCH SUMMARY ===")
    print(f"Passwords graded: {stats['total_passwords']}")
    print(f"Average score: {stats['mean_score']:.2f}")
    print(f"Grade distribution: {stats['grade_distribution']}")

    if args.json_output:
        payload = {
            "model_metadata": model["metadata"],
            "results": results,
            "summary": stats,
        }
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"Detailed output written to: {output_path}")


if __name__ == "__main__":
    main()
