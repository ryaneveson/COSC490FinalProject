
# Top-level function for multiprocessing compatibility
def _score_pwd_with_counts(args):
    pwd, counts = args
    from collections import Counter, defaultdict  # for Windows compatibility
    return (pwd, password_score(pwd, counts))
import os
import multiprocessing
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Any

DATA_FILE = str(Path(__file__).resolve().parent.parent / "data" / "archive" / "100k-most-used-passwords-NCSC.txt")


def build_ngram_counts(data_file: str, verbose=False, progress_interval=100000):
    unigram = Counter()
    bigram = defaultdict(Counter)
    trigram = defaultdict(Counter)
    total_passwords = 0

    # Count total lines for progress bar
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found")
        return {
            "total_passwords": 0,
            "unigram": unigram,
            "bigram": bigram,
            "trigram": trigram,
        }
    with open(data_file, "r", encoding="utf-8", errors="replace") as fd:
        total_lines = sum(1 for _ in fd)

    if tqdm:
        pbar = tqdm(total=total_lines, desc="Building n-gram model", unit="pwds")
    else:
        pbar = None

    with open(data_file, "r", encoding="utf-8", errors="replace") as fd:
        for i, raw_line in enumerate(fd, start=1):
            line = raw_line.rstrip("\r\n")
            if not line:
                continue
            pwd = line
            total_passwords += 1
            unigram.update(pwd)
            for a, b in zip(pwd, pwd[1:]):
                bigram[a][b] += 1
            for (a, b), c in zip(zip(pwd, pwd[1:]), pwd[2:]):
                trigram[(a, b)][c] += 1
            if pbar:
                pbar.update(1)
            elif verbose and total_passwords % progress_interval == 0:
                print(f"  {total_passwords:,} passwords processed")
    if pbar:
        pbar.close()
    return {
        "total_passwords": total_passwords,
        "unigram": unigram,
        "bigram": bigram,
        "trigram": trigram,
    }


def build_summary(counts, top_k=20):
    """Build summary statistics for JSON output"""
    unigram = counts["unigram"]
    bigram = counts["bigram"]
    trigram = counts["trigram"]

    summary = {
        "total_passwords": counts["total_passwords"],
        "vocab_size": len(unigram),
        "top_unigram": unigram.most_common(top_k),
        "bigram_conditional": {},
        "trigram_conditional": {},
    }

    for a, targets in bigram.items():
        total = sum(targets.values())
        rows = []
        for b, cnt in targets.most_common(top_k):
            rows.append({"next": b, "count": cnt, "prob": cnt / total})
        summary["bigram_conditional"][a] = {"total": total, "top": rows}

    for ab, targets in trigram.items():
        total = sum(targets.values())
        rows = []
        for c, cnt in targets.most_common(top_k):
            rows.append({"next": c, "count": cnt, "prob": cnt / total})
        summary["trigram_conditional"]["".join(ab)] = {"total": total, "top": rows}

    return summary


def compute_full_stats(base_dir: Path, folders, counts, verbose=False, progress_interval=100000):

    # Gather all passwords for parallel scoring from the new dataset file
    all_passwords = []
    pwd_lengths = []
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found")
        return {
            "total_passwords": 0,
            "total_chars": 0,
            "length_counts": Counter(),
            "predictability_scores": [],
            "sample_passwords": [],
        }
    with open(DATA_FILE, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            pwd = line.strip()
            if not pwd:
                continue
            all_passwords.append(pwd)
            pwd_lengths.append(len(pwd))

    total_passwords = len(all_passwords)
    total_chars = sum(pwd_lengths)
    length_counts = Counter(pwd_lengths)

    # Multiprocessing for scoring
    cpu_count = max(1, multiprocessing.cpu_count() - 1)
    print("Starting password scoring (Step 5)...")
    if tqdm:
        pbar = tqdm(total=total_passwords, desc="Scoring passwords", unit="pwds")
    else:
        pbar = None
    predictability_scores = []
    sample_passwords = []
    # Prepare arguments as (pwd, counts) tuples for each password
    args_iter = ((pwd, counts) for pwd in all_passwords)
    with multiprocessing.Pool(cpu_count) as pool:
        for pwd, score in pool.imap(_score_pwd_with_counts, args_iter, chunksize=1_000_000):
            predictability_scores.append(score["predictability"])
            if len(sample_passwords) < 20 and len(pwd) > 5:
                sample_passwords.append((pwd, score))
            if pbar:
                pbar.update(1)
            elif len(predictability_scores) % progress_interval == 0:
                print(f"  {len(predictability_scores):,} passwords scored...")
    if pbar:
        pbar.close()
    print(f"Finished scoring {len(predictability_scores):,} passwords.")

    return {
        "total_passwords": total_passwords,
        "total_chars": total_chars,
        "length_counts": length_counts,
        "predictability_scores": predictability_scores,
        "sample_passwords": sample_passwords,
    }


def generate_report(counts, stats, target_folders):
    unigram = counts["unigram"]
    bigram = counts["bigram"]
    trigram = counts["trigram"]

    total_passwords = stats["total_passwords"]
    total_chars = stats["total_chars"]
    predictability_scores = stats["predictability_scores"]

    # Compute stats
    mean_pred = sum(predictability_scores) / len(predictability_scores) if predictability_scores else 0
    sorted_pred = sorted(predictability_scores)
    median_pred = sorted_pred[len(sorted_pred)//2] if sorted_pred else 0
    p10 = sorted_pred[int(0.1 * len(sorted_pred))] if sorted_pred else 0
    p90 = sorted_pred[int(0.9 * len(sorted_pred))] if sorted_pred else 0

    # Predictability distribution
    pred_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    pred_dist = Counter()
    for score in predictability_scores:
        for i in range(len(pred_bins)-1):
            if pred_bins[i] <= score < pred_bins[i+1]:
                pred_dist[f"{pred_bins[i]}–{pred_bins[i+1]}"] += 1
                break

    # Top characters
    top_chars = unigram.most_common(20)

    # Top transitions (most common)
    all_transitions = []
    for a, targets in bigram.items():
        for b, cnt in targets.items():
            all_transitions.append((a, b, cnt))
    top_transitions = sorted(all_transitions, key=lambda x: x[2], reverse=True)[:20]

    # Highest probability transitions (min 1000 occurrences)
    high_prob_trans = []
    for a, targets in bigram.items():
        total_a = sum(targets.values())
        for b, cnt in targets.items():
            if cnt >= 1000:
                prob = cnt / total_a
                high_prob_trans.append((a, b, prob, cnt))
    high_prob_trans.sort(key=lambda x: x[2], reverse=True)
    top_high_prob = high_prob_trans[:20]

    # Length distribution (top 30)
    top_lengths = stats["length_counts"].most_common(30)

    # Sample passwords
    sample_table = []
    for pwd, score in stats["sample_passwords"][:20]:
        sample_table.append({
            "password": pwd,
            "predictability": f"{score['predictability']:.2f}"
        })

    # Build markdown
    md = f"""# Step 5: Probabilistic Prediction Report

Data source: file `100k-most-used-passwords-NCSC.txt`.

## Executive Summary

- **Passwords Trained On**: {total_passwords:,}
- **Passwords Evaluated**: {total_passwords:,}
- **Total Characters Processed**: {total_chars:,}
- **Unique Characters**: {len(unigram):,}
- **Mean Predictability Score**: {mean_pred:.4f}
- **Median Predictability Score**: {median_pred:.4f}
- **10th / 90th Percentile**: {p10:.4f} / {p90:.4f}

## Methodology

A character-level n-gram language model captures how likely each character is given the previous one(s):

1. **Bigram**: P(c_n | c_{{n-1}})
2. **Trigram**: P(c_n | c_{{n-2}}, c_{{n-1}})
3. **Interpolated**: 0.4 × P_bigram + 0.6 × P_trigram
4. **Laplace smoothing** handles unseen transitions
5. Predictability score scaled 0–100 from average log₂-probability per transition

## Predictability Score Distribution

| Score Range | Count | % |
|-------------|-------|---|
"""
    for bin_name, count in sorted(pred_dist.items()):
        pct = count / total_passwords * 100
        md += f"| {bin_name} | {count:,} | {pct:.2f}% |\n"

    md += "\n## Top 20 Character Frequencies\n\n| Rank | Char | Count | % |\n|------|------|-------|---|\n"
    for rank, (char, count) in enumerate(top_chars, 1):
        pct = count / sum(unigram.values()) * 100
        md += f"| {rank} | `{char}` | {count:,} | {pct:.3f}% |\n"

    md += "\n## Top 20 Most Common Transitions\n\n| From | To | Count | P |\n|------|----|-------|---|\n"
    for a, b, cnt in top_transitions:
        p = cnt / sum(bigram[a].values())
        md += f"| `{a}` | `{b}` | {cnt:,} | {p:.4f} |\n"

    md += "\n## Top 20 Highest Probability Transitions\n\nGiven the preceding character, these next characters are most predictable (min 1,000 occurrences).\n\n| From | To | P | Count |\n|------|----|---|-------|\n"
    for a, b, p, cnt in top_high_prob:
        md += f"| `{a}` | `{b}` | {p:.4f} | {cnt:,} |\n"

    md += "\n## Sample Passwords with Scores\n\n| Password | Predictability |\n|----------|----------------|\n"
    for item in sample_table:
        md += f"| `{item['password']}` | {item['predictability']} |\n"

    md += "\n## Password Length Distribution (Top 30)\n\n| Length | Count |\n|--------|-------|\n"
    for length, count in top_lengths:
        md += f"| {length} | {count:,} |\n"

    return md


def password_score(password: str, counts, smoothing=1e-6):
    unigram = counts.get("unigram", Counter())
    bigram = counts.get("bigram", defaultdict(Counter))
    trigram = counts.get("trigram", defaultdict(lambda: defaultdict(Counter)))

    vocab_size = max(1, len(unigram))

    # Interpolated model: 0.4 * bigram + 0.6 * trigram with Laplace smoothing
    log_prob = 0.0
    transitions = 0

    for i in range(1, len(password)):
        prev_char = password[i-1]
        curr_char = password[i]

        # Bigram prob
        count_ab = bigram.get(prev_char, {}).get(curr_char, 0)
        count_a = sum(bigram.get(prev_char, {}).values())
        bigram_prob = (count_ab + smoothing) / (count_a + smoothing * vocab_size)

        # Trigram prob (if i >= 2)
        if i >= 2:
            prev_prev = password[i-2]
            count_abc = trigram.get((prev_prev, prev_char), {}).get(curr_char, 0)
            count_ab_total = sum(trigram.get((prev_prev, prev_char), {}).values())
            trigram_prob = (count_abc + smoothing) / (count_ab_total + smoothing * vocab_size)
        else:
            trigram_prob = bigram_prob  # Fallback for first transition

        # Interpolated
        prob = 0.4 * bigram_prob + 0.6 * trigram_prob
        log_prob += math.log2(prob)  # Use log2 for predictability score
        transitions += 1

    if transitions == 0:
        return {"length": len(password), "log_prob": 0.0, "predictability": 0.0}

    avg_log_prob = log_prob / transitions
    # Predictability score: scale to 0-100 (higher = more predictable)
    # Scaling factor 1.4: tuned so truly random passwords score ~40+ base
    # (previously *2 over-penalized randomness, capping strong passwords at ~86)
    predictability = max(0, min(100, -avg_log_prob * 1.4))

    return {
        "length": len(password),
        "log_prob": log_prob,
        "avg_log_prob": avg_log_prob,
        "predictability": predictability,
    }


def main():
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description="Build character-level n-gram model and generate Step 5 report")
    parser.add_argument("--data_dir", default=str(script_dir.parent / "data" / "archive"),
                        help="Base data archive directory")
    parser.add_argument("--output", default=str(script_dir / "STEP5_PROBABILISTIC_REPORT.md"),
                        help="Markdown report output")
    parser.add_argument("--json_output", default=str(script_dir / "step5_probabilistic_summary.json"),
                        help="JSON summary output")
    parser.add_argument("--progress_interval", type=int, default=100000, help="Count interval for verbose progress")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (script_dir / args.output).resolve()

    json_output_path = Path(args.json_output)
    if not json_output_path.is_absolute():
        json_output_path = (script_dir / args.json_output).resolve()

    # Build n-gram model
    if args.verbose:
        print("Building n-gram model...")
    counts = build_ngram_counts(DATA_FILE, verbose=args.verbose, progress_interval=args.progress_interval)

    # Compute full stats
    if args.verbose:
        print("Computing predictability scores...")
    stats = compute_full_stats(None, None, counts, verbose=args.verbose, progress_interval=args.progress_interval)

    # Build summary (for JSON)
    if args.verbose:
        print("Building summary...")
    summary = build_summary(counts, top_k=20)

    # Save JSON summary AND full n-gram counts
    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    with json_output_path.open("w", encoding="utf-8") as fd:
        # Save both summary and full counts for downstream use
        # Recursively ensure all values are dicts, not ints
        def recursive_safe_dict(obj):
            if isinstance(obj, dict):
                return {k: recursive_safe_dict(v) for k, v in obj.items()}
            elif isinstance(obj, Counter):
                return {k: recursive_safe_dict(v) for k, v in obj.items()}
            elif isinstance(obj, int):
                return obj
            else:
                return int(obj) if isinstance(obj, float) else obj

        bigram_json = {k: recursive_safe_dict(v) for k, v in counts["bigram"].items()}
        trigram_json = {str(k): recursive_safe_dict(v) for k, v in counts["trigram"].items()}

        json.dump({
            **summary,
            "unigram": {k: v for k, v in counts["unigram"].items()},
            "bigram": bigram_json,
            "trigram": trigram_json,
        }, fd, indent=2, ensure_ascii=False)

    # Generate and save report
    if args.verbose:
        print("Generating report...")
    report_md = generate_report(counts, stats, ["100k-most-used-passwords-NCSC.txt"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fd:
        fd.write(report_md)

    if args.verbose:
        print(f"Saved JSON summary to {json_output_path}")
        print(f"Saved report to {output_path}")
        print("Done.")

    # Example scoring for sanity check
    examples = ["Password123!", "123456", "!Qaz2wsx"]
    print("Example scores:")
    for ex in examples:
        s = password_score(ex, counts)
        print(f"  {ex!r}: predictability={s['predictability']:.2f}")


if __name__ == "__main__":
    main()
