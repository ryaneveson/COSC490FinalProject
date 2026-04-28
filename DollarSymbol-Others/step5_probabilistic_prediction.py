import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


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

START_TOKEN = "<s>"
END_TOKEN = "</s>"
SURPRISAL_STATS_SAMPLE_SIZE = 200000


def is_lfs_pointer(file_path: Path) -> bool:
    try:
        with file_path.open("r", encoding="utf-8", errors="replace") as handle:
            first_line = handle.readline().strip()
            return first_line == "version https://git-lfs.github.com/spec/v1"
    except OSError:
        return False


def iter_passwords(base_dir: Path, max_passwords: int | None = None):
    files_scanned = 0
    files_skipped_lfs = 0
    yielded = 0

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
                if not password:
                    continue
                yield password
                yielded += 1
                if max_passwords is not None and yielded >= max_passwords:
                    print("\nReached max-passwords limit.")
                    print(f"Files scanned: {files_scanned}")
                    if files_skipped_lfs:
                        print(f"Files skipped (Git LFS pointers): {files_skipped_lfs}")
                    return

    print(f"\nFiles scanned: {files_scanned}")
    if files_skipped_lfs:
        print(f"Files skipped (Git LFS pointers): {files_skipped_lfs}")


def iter_balanced_sample_passwords(base_dir: Path, sample_size: int):
    if sample_size <= 0:
        return

    per_folder_limit = math.ceil(sample_size / max(len(TARGET_FOLDERS), 1))
    yielded = 0

    for folder in TARGET_FOLDERS:
        if yielded >= sample_size:
            break

        file_path = base_dir / folder / f"{folder}.txt"
        if not file_path.exists() or is_lfs_pointer(file_path):
            continue

        folder_count = 0
        with file_path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                password = raw_line.rstrip("\r\n")
                if not password:
                    continue
                yield password, folder
                yielded += 1
                folder_count += 1
                if yielded >= sample_size or folder_count >= per_folder_limit:
                    break


def train_model(base_dir: Path, max_passwords: int | None = None):
    unigram_counts = Counter()
    bigram_counts = defaultdict(Counter)
    trigram_counts = defaultdict(Counter)

    vocabulary = set()
    total_passwords = 0
    total_transitions = 0

    for password in iter_passwords(base_dir, max_passwords=max_passwords):
        total_passwords += 1
        sequence = [START_TOKEN, START_TOKEN, *list(password), END_TOKEN]

        for idx in range(2, len(sequence)):
            prev2 = sequence[idx - 2]
            prev1 = sequence[idx - 1]
            nxt = sequence[idx]

            unigram_counts[nxt] += 1
            bigram_counts[prev1][nxt] += 1
            trigram_counts[(prev2, prev1)][nxt] += 1

            vocabulary.add(nxt)
            total_transitions += 1

    return {
        "metadata": {
            "model_type": "character_ngram_interpolated",
            "version": 2,
            "total_passwords": total_passwords,
            "total_transitions": total_transitions,
            "target_folders": TARGET_FOLDERS,
        },
        "tokens": {
            "start": START_TOKEN,
            "end": END_TOKEN,
        },
        "vocabulary": sorted(vocabulary),
        "unigram_counts": dict(unigram_counts),
        "bigram_counts": [
            {
                "context": context,
                "next_counts": dict(next_counts),
            }
            for context, next_counts in bigram_counts.items()
        ],
        "trigram_counts": [
            {
                "context": [context[0], context[1]],
                "next_counts": dict(next_counts),
            }
            for context, next_counts in trigram_counts.items()
        ],
    }


def smoothed_probability(next_counts: dict, token: str, alpha: float, vocab_size: int) -> float:
    total = sum(next_counts.values())
    count = next_counts.get(token, 0)
    return (count + alpha) / (total + alpha * vocab_size)


def build_lookups(model: dict) -> tuple[dict, dict]:
    bigram_lookup = {item["context"]: item["next_counts"] for item in model["bigram_counts"]}
    trigram_lookup = {
        (item["context"][0], item["context"][1]): item["next_counts"] for item in model["trigram_counts"]
    }
    return bigram_lookup, trigram_lookup


def transition_probability(
    model: dict,
    bigram_lookup: dict,
    trigram_lookup: dict,
    prev2: str,
    prev1: str,
    nxt: str,
    alpha: float,
) -> float:
    vocab_size = len(model["vocabulary"])
    p_uni = smoothed_probability(model["unigram_counts"], nxt, alpha, vocab_size)
    p_bi = smoothed_probability(bigram_lookup.get(prev1, {}), nxt, alpha, vocab_size)
    p_tri = smoothed_probability(trigram_lookup.get((prev2, prev1), {}), nxt, alpha, vocab_size)
    return 0.60 * p_tri + 0.30 * p_bi + 0.10 * p_uni


def average_surprisal(password: str, model: dict, bigram_lookup: dict, trigram_lookup: dict, alpha: float) -> float:
    sequence = [START_TOKEN, START_TOKEN, *list(password), END_TOKEN]
    surprisal_sum = 0.0
    transition_count = 0

    for idx in range(2, len(sequence)):
        prev2 = sequence[idx - 2]
        prev1 = sequence[idx - 1]
        nxt = sequence[idx]
        probability = transition_probability(model, bigram_lookup, trigram_lookup, prev2, prev1, nxt, alpha)
        surprisal_sum += -math.log2(probability)
        transition_count += 1

    return surprisal_sum / max(transition_count, 1)


def summarize_surprisal_stats(
    base_dir: Path,
    model: dict,
    alpha: float,
    max_passwords: int,
    training_max_passwords: int | None,
) -> dict | None:
    if max_passwords <= 0:
        return None

    bigram_lookup, trigram_lookup = build_lookups(model)
    values = []
    folder_counts = {folder: 0 for folder in TARGET_FOLDERS}
    sampling_strategy = "balanced_per_folder_prefix"

    if training_max_passwords is not None and training_max_passwords > 0:
        sampling_strategy = "training_prefix"
        sample_limit = min(max_passwords, training_max_passwords)
        for password in iter_passwords(base_dir, max_passwords=sample_limit):
            values.append(average_surprisal(password, model, bigram_lookup, trigram_lookup, alpha))
    else:
        for password, folder in iter_balanced_sample_passwords(base_dir, sample_size=max_passwords):
            values.append(average_surprisal(password, model, bigram_lookup, trigram_lookup, alpha))
            folder_counts[folder] += 1

    if not values:
        return None

    values.sort()
    count = len(values)
    mean = sum(values) / count
    variance = sum((value - mean) ** 2 for value in values) / count
    std = math.sqrt(variance)

    def percentile(p: float) -> float:
        if count == 1:
            return values[0]
        index = (count - 1) * p
        low = int(index)
        high = min(low + 1, count - 1)
        weight = index - low
        return values[low] * (1 - weight) + values[high] * weight

    return {
        "sample_size": count,
        "alpha": alpha,
        "sampling_strategy": sampling_strategy,
        "folder_counts": folder_counts,
        "mean": round(mean, 6),
        "std": round(std, 6),
        "p10": round(percentile(0.10), 6),
        "p25": round(percentile(0.25), 6),
        "p50": round(percentile(0.50), 6),
        "p75": round(percentile(0.75), 6),
        "p90": round(percentile(0.90), 6),
    }


def predict_next_chars(
    model: dict,
    context: str,
    top_n: int,
    alpha: float,
    trigram_weight: float,
    bigram_weight: float,
    unigram_weight: float,
):
    vocabulary = model["vocabulary"]
    vocab_size = len(vocabulary)

    unigram_counts = model["unigram_counts"]
    bigram_lookup = {item["context"]: item["next_counts"] for item in model["bigram_counts"]}
    trigram_lookup = {
        (item["context"][0], item["context"][1]): item["next_counts"] for item in model["trigram_counts"]
    }

    prev1 = context[-1] if context else START_TOKEN
    prev2 = context[-2] if len(context) >= 2 else START_TOKEN

    bigram_next = bigram_lookup.get(prev1, {})
    trigram_next = trigram_lookup.get((prev2, prev1), {})

    predictions = []
    for candidate in vocabulary:
        p_uni = smoothed_probability(unigram_counts, candidate, alpha, vocab_size)
        p_bi = smoothed_probability(bigram_next, candidate, alpha, vocab_size)
        p_tri = smoothed_probability(trigram_next, candidate, alpha, vocab_size)
        p = trigram_weight * p_tri + bigram_weight * p_bi + unigram_weight * p_uni
        predictions.append((candidate, p))

    predictions.sort(key=lambda item: item[1], reverse=True)
    return predictions[:top_n]


def run_step5(
    base_dir: Path,
    output_path: Path,
    max_passwords: int | None,
    top_n: int,
    context: str | None,
    alpha: float,
):
    model = train_model(base_dir, max_passwords=max_passwords)

    print("\n=== STEP 5: PROBABILISTIC PREDICTION (CHARACTER N-GRAM) ===")
    print(f"Target folders: {', '.join(TARGET_FOLDERS)}")
    print(f"Total passwords processed: {model['metadata']['total_passwords']:,}")
    print(f"Total transitions observed: {model['metadata']['total_transitions']:,}")

    if model["metadata"]["total_passwords"] == 0:
        print("No passwords processed. If you expected data, run `git lfs pull` first.")
        return

    surprisal_stats = summarize_surprisal_stats(
        base_dir=base_dir,
        model=model,
        alpha=alpha,
        max_passwords=SURPRISAL_STATS_SAMPLE_SIZE,
        training_max_passwords=max_passwords,
    )
    if surprisal_stats is not None:
        model["metadata"]["surprisal_stats"] = surprisal_stats
        print(
            "Surprisal stats (sample size "
            f"{surprisal_stats['sample_size']:,}): mean={surprisal_stats['mean']:.3f}, std={surprisal_stats['std']:.3f}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(model, handle, indent=2)
    print(f"Model saved to: {output_path}")

    query_context = context if context is not None else ""
    print(f"\nTop {top_n} next-character predictions for context: {query_context!r}")
    predictions = predict_next_chars(
        model=model,
        context=query_context,
        top_n=top_n,
        alpha=alpha,
        trigram_weight=0.60,
        bigram_weight=0.30,
        unigram_weight=0.10,
    )
    for token, probability in predictions:
        label = "<END>" if token == END_TOKEN else token
        print(f"- {label!r}: {probability:.6f}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Step 5 probabilistic prediction with character-level n-gram transitions"
    )
    parser.add_argument(
        "--base-dir",
        default="data/archive",
        help="Base dataset directory containing archive subfolders (default: data/archive)",
    )
    parser.add_argument(
        "--output",
        default="DollarSymbol-Others/models/character_ngram_model.json",
        help="Output path for trained model JSON",
    )
    parser.add_argument(
        "--max-passwords",
        type=int,
        default=None,
        help="Optional limit for number of passwords to process",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Top N next-character predictions to print (default: 10)",
    )
    parser.add_argument(
        "--context",
        default=None,
        help="Optional context string for next-character prediction preview",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Laplace smoothing constant (default: 0.5)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_step5(
        base_dir=Path(args.base_dir),
        output_path=Path(args.output),
        max_passwords=args.max_passwords,
        top_n=args.top,
        context=args.context,
        alpha=args.alpha,
    )


if __name__ == "__main__":
    main()
