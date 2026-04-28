"""
Step 5: Probabilistic Prediction
Character-level n-gram language model for password predictability analysis.

Builds bigram and trigram transition probability matrices from the password
dataset, then analyzes how predictable passwords are character-by-character.

No external ML libraries required — uses only Python standard library.

Usage:
    python Step5.py --base-dir data/archive
    python Step5.py --base-dir data/archive --sample 100000
"""

import json
import math
import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import List


TARGET_FOLDERS = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "A", "B", "C", "D",
]

START_TOKEN = "<S>"
END_TOKEN = "<E>"


class CharNgramModel:
    """Character-level n-gram language model trained on passwords."""

    def __init__(self):
        self.char_counts = Counter()
        self.total_chars = 0

        self.bigram_counts = defaultdict(Counter)
        self.bigram_context_totals = Counter()

        self.trigram_counts = defaultdict(Counter)
        self.trigram_context_totals = Counter()

        self.password_count = 0
        self.password_lengths = Counter()

    def train_on_password(self, password: str):
        """Update n-gram counts from a single password."""
        self.password_count += 1
        self.password_lengths[len(password)] += 1

        chars = [START_TOKEN] + list(password) + [END_TOKEN]

        for i, char in enumerate(chars):
            if char not in (START_TOKEN, END_TOKEN):
                self.char_counts[char] += 1
                self.total_chars += 1

            if i > 0:
                context = chars[i - 1]
                self.bigram_counts[context][char] += 1
                self.bigram_context_totals[context] += 1

            if i > 1:
                context = (chars[i - 2], chars[i - 1])
                ctx_key = f"{chars[i-2]}|{chars[i-1]}"
                self.trigram_counts[ctx_key][char] += 1
                self.trigram_context_totals[ctx_key] += 1

    @property
    def vocab_size(self) -> int:
        return len(self.char_counts) + 2

    def bigram_prob(self, prev_char: str, curr_char: str) -> float:
        """P(curr_char | prev_char) with Laplace smoothing."""
        count = self.bigram_counts[prev_char][curr_char]
        total = self.bigram_context_totals[prev_char]
        return (count + 1) / (total + self.vocab_size)

    def trigram_prob(self, prev2: str, prev1: str, curr: str) -> float:
        """P(curr | prev2, prev1) with Laplace smoothing."""
        ctx_key = f"{prev2}|{prev1}"
        count = self.trigram_counts[ctx_key][curr]
        total = self.trigram_context_totals[ctx_key]
        return (count + 1) / (total + self.vocab_size)

    def password_log_prob_bigram(self, password: str) -> float:
        """Average log2 probability per transition under the bigram model."""
        chars = [START_TOKEN] + list(password) + [END_TOKEN]
        log_sum = 0.0
        n = 0
        for i in range(1, len(chars)):
            p = self.bigram_prob(chars[i - 1], chars[i])
            log_sum += math.log2(p) if p > 0 else -30.0
            n += 1
        return log_sum / n if n else -30.0

    def password_log_prob_trigram(self, password: str) -> float:
        """Average log2 probability per transition under the trigram model."""
        chars = [START_TOKEN, START_TOKEN] + list(password) + [END_TOKEN]
        log_sum = 0.0
        n = 0
        for i in range(2, len(chars)):
            p = self.trigram_prob(chars[i - 2], chars[i - 1], chars[i])
            log_sum += math.log2(p) if p > 0 else -30.0
            n += 1
        return log_sum / n if n else -30.0

    def password_predictability(self, password: str) -> float:
        """
        Predictability score 0-100 (higher = more predictable).
        Uses interpolated bigram (0.4) + trigram (0.6) model.
        """
        LAMBDA_BI = 0.4
        LAMBDA_TRI = 0.6

        chars = [START_TOKEN, START_TOKEN] + list(password) + [END_TOKEN]
        log_sum = 0.0
        n = 0

        for i in range(2, len(chars)):
            bi = self.bigram_prob(chars[i - 1], chars[i])
            tri = self.trigram_prob(chars[i - 2], chars[i - 1], chars[i])
            interpolated = LAMBDA_BI * bi + LAMBDA_TRI * tri
            log_sum += math.log2(interpolated) if interpolated > 0 else -30.0
            n += 1

        if n == 0:
            return 50.0

        avg_log = log_sum / n
        # avg_log ranges roughly from -10 (random) to -1 (very predictable)
        # Map to 0–100 where 100 = extremely predictable
        score = max(0.0, min(100.0, (avg_log + 10.0) / 9.0 * 100.0))
        return score

    def get_top_transitions(self, n: int = 30) -> List[dict]:
        """Top n most frequent character-to-character transitions."""
        transitions = []
        for ctx, nexts in self.bigram_counts.items():
            total = self.bigram_context_totals[ctx]
            for nxt, count in nexts.most_common(3):
                transitions.append({
                    "from": ctx,
                    "to": nxt,
                    "count": count,
                    "probability": round(count / total, 4) if total else 0,
                })
        transitions.sort(key=lambda x: x["count"], reverse=True)
        return transitions[:n]

    def get_highest_prob_transitions(self, min_count: int = 1000, n: int = 30) -> List[dict]:
        """Transitions with highest conditional probability (min occurrence filter)."""
        transitions = []
        for ctx, nexts in self.bigram_counts.items():
            total = self.bigram_context_totals[ctx]
            if total < min_count:
                continue
            for nxt, count in nexts.items():
                prob = count / total if total else 0
                transitions.append({
                    "from": ctx,
                    "to": nxt,
                    "count": count,
                    "context_total": total,
                    "probability": round(prob, 4),
                })
        transitions.sort(key=lambda x: x["probability"], reverse=True)
        return transitions[:n]

    def to_serializable(self) -> dict:
        """Serialize model to a JSON-safe dict (for Step 6 to reload)."""
        bigram_data = {}
        for ctx, nexts in self.bigram_counts.items():
            significant = {c: cnt for c, cnt in nexts.items() if cnt > 5}
            if significant:
                bigram_data[ctx] = significant

        trigram_data = {}
        for ctx_key, nexts in self.trigram_counts.items():
            significant = {c: cnt for c, cnt in nexts.items() if cnt > 10}
            if significant:
                trigram_data[ctx_key] = significant

        return {
            "password_count": self.password_count,
            "total_chars": self.total_chars,
            "vocab_size": self.vocab_size,
            "char_counts": dict(self.char_counts.most_common(300)),
            "bigram_counts": bigram_data,
            "bigram_context_totals": dict(self.bigram_context_totals),
            "trigram_counts": trigram_data,
            "trigram_context_totals": dict(self.trigram_context_totals),
        }


class ProbabilisticPredictionAnalyzer:
    """Step 5: Analyze character transition probabilities in passwords."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.model = CharNgramModel()
        self.results = {}

    def _iter_passwords(self):
        """Iterate through all passwords from 0–D folders."""
        for folder in TARGET_FOLDERS:
            fp = self.base_dir / folder / f"{folder}.txt"
            if not fp.exists():
                print(f"  {fp} not found")
                continue
            print(f"Processing {folder}...")
            try:
                with fp.open("r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        pw = line.strip()
                        if pw:
                            yield pw
            except Exception as e:
                print(f"  Error reading {fp}: {e}")

    def analyze(self, sample_size: int = None):
        """Build the n-gram model and evaluate password predictability."""
        print("\n" + "=" * 80)
        print("STEP 5: PROBABILISTIC PREDICTION (Character N-gram Model)")
        print("=" * 80 + "\n")

        # --- Phase 1: Train ------------------------------------------------
        print("Phase 1: Building character n-gram model ...\n")
        total = 0
        for pw in self._iter_passwords():
            if sample_size and total >= sample_size:
                break
            self.model.train_on_password(pw)
            total += 1
            if total % 500_000 == 0:
                print(f"  Trained on {total:,} passwords ...")

        print(f"\n  Model trained on {total:,} passwords")
        print(f"  Total characters processed: {self.model.total_chars:,}")
        print(f"  Unique characters seen: {len(self.model.char_counts):,}")

        # --- Phase 2: Evaluate predictability on all passwords ----------------
        print("\nPhase 2: Evaluating password predictability ...\n")
        predictability_scores = []
        bigram_scores = []
        trigram_scores = []
        score_buckets = Counter()
        sample_graded = []

        eval_count = 0
        for pw in self._iter_passwords():
            if sample_size and eval_count >= sample_size:
                break

            bi = self.model.password_log_prob_bigram(pw)
            tri = self.model.password_log_prob_trigram(pw)
            pred = self.model.password_predictability(pw)

            bigram_scores.append(bi)
            trigram_scores.append(tri)
            predictability_scores.append(pred)
            score_buckets[int(pred // 10) * 10] += 1

            if len(sample_graded) < 100:
                sample_graded.append({
                    "password": pw[:20],
                    "bigram_avg_log_prob": round(bi, 4),
                    "trigram_avg_log_prob": round(tri, 4),
                    "predictability": round(pred, 2),
                })

            eval_count += 1
            if eval_count % 500_000 == 0:
                print(f"  Evaluated {eval_count:,} passwords ...")

        # --- Compute statistics ---------------------------------------------
        if predictability_scores:
            s = sorted(predictability_scores)
            stats = {
                "mean": round(sum(s) / len(s), 4),
                "median": round(s[len(s) // 2], 4),
                "p10": round(s[int(len(s) * 0.10)], 4),
                "p90": round(s[int(len(s) * 0.90)], 4),
                "min": round(s[0], 4),
                "max": round(s[-1], 4),
            }
            avg_bi = round(sum(bigram_scores) / len(bigram_scores), 4)
            avg_tri = round(sum(trigram_scores) / len(trigram_scores), 4)
        else:
            stats = {k: 0 for k in ("mean", "median", "p10", "p90", "min", "max")}
            avg_bi = avg_tri = 0

        char_freq = self.model.char_counts.most_common(50)
        tc = self.model.total_chars
        char_freq_pct = [
            {"char": c, "count": cnt, "percentage": round(cnt / tc * 100, 4)}
            for c, cnt in char_freq
        ]

        top_transitions = self.model.get_top_transitions(30)
        hi_prob = self.model.get_highest_prob_transitions(min_count=1000, n=30)

        length_dist = dict(sorted(
            self.model.password_lengths.items(), key=lambda x: int(x[0])
        )[:50])

        self.results = {
            "total_passwords_trained": total,
            "total_passwords_evaluated": eval_count,
            "total_chars": self.model.total_chars,
            "unique_chars": len(self.model.char_counts),
            "predictability_stats": stats,
            "avg_bigram_log_prob": avg_bi,
            "avg_trigram_log_prob": avg_tri,
            "score_distribution": dict(sorted(score_buckets.items())),
            "top_char_frequencies": char_freq_pct,
            "top_transitions_by_count": top_transitions,
            "highest_probability_transitions": hi_prob,
            "sample_passwords_graded": sample_graded[:30],
            "password_length_distribution": length_dist,
        }

        self._print_results()

    # ------------------------------------------------------------------ #
    #  Console output                                                      #
    # ------------------------------------------------------------------ #
    def _print_results(self):
        r = self.results
        print("\n" + "=" * 80)
        print("PROBABILISTIC PREDICTION RESULTS")
        print("=" * 80 + "\n")

        print(" MODEL OVERVIEW")
        print("-" * 80)
        print(f"Passwords trained on:    {r['total_passwords_trained']:,}")
        print(f"Passwords evaluated:     {r['total_passwords_evaluated']:,}")
        print(f"Total characters:        {r['total_chars']:,}")
        print(f"Unique characters:       {r['unique_chars']:,}")
        print()

        st = r["predictability_stats"]
        print(" PREDICTABILITY STATISTICS")
        print("-" * 80)
        print(f"Mean score:   {st['mean']:.4f}")
        print(f"Median:       {st['median']:.4f}")
        print(f"10th %ile:    {st['p10']:.4f}")
        print(f"90th %ile:    {st['p90']:.4f}")
        print(f"Min / Max:    {st['min']:.4f} / {st['max']:.4f}")
        print(f"Avg bigram log-prob:   {r['avg_bigram_log_prob']:.4f}")
        print(f"Avg trigram log-prob:  {r['avg_trigram_log_prob']:.4f}")
        print()

        print(" PREDICTABILITY SCORE DISTRIBUTION")
        print("-" * 80)
        te = r["total_passwords_evaluated"]
        for bucket, count in sorted(r["score_distribution"].items()):
            pct = count / te * 100 if te else 0
            bar = "\u2588" * int(pct / 2)
            print(f"  {bucket:3d}-{bucket + 10:3d}: {count:10,} ({pct:6.2f}%) {bar}")
        print()

        print(" TOP 20 CHARACTER FREQUENCIES")
        print("-" * 80)
        for item in r["top_char_frequencies"][:20]:
            c = item["char"]
            disp = c if c.isprintable() and len(c) == 1 else repr(c)
            print(f"  '{disp}': {item['count']:12,} ({item['percentage']:6.3f}%)")
        print()

        print(" TOP 20 MOST COMMON TRANSITIONS")
        print("-" * 80)
        for t in r["top_transitions_by_count"][:20]:
            print(f"  {t['from']!r:8s} -> {t['to']!r:8s}: "
                  f"{t['count']:10,} (P={t['probability']:.4f})")
        print()

        print(" TOP 20 HIGHEST PROBABILITY TRANSITIONS (min 1 000 occurrences)")
        print("-" * 80)
        for t in r["highest_probability_transitions"][:20]:
            print(f"  {t['from']!r:8s} -> {t['to']!r:8s}: "
                  f"P={t['probability']:.4f}  (n={t['count']:,})")
        print()

        print(" SAMPLE PASSWORDS WITH SCORES")
        print("-" * 80)
        hdr = f"{'Password':<22s} {'Bi-logP':>9s} {'Tri-logP':>9s} {'Pred':>7s}"
        print(hdr)
        print("-" * len(hdr))
        for s in r["sample_passwords_graded"][:20]:
            print(f"{s['password']:<22s} {s['bigram_avg_log_prob']:>9.4f} "
                  f"{s['trigram_avg_log_prob']:>9.4f} {s['predictability']:>7.2f}")

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #
    def save_results(self, output_dir: str = "."):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        res_file = out / "step5_probabilistic_results.json"
        with open(res_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n Results saved to {res_file}")

        model_file = out / "step5_ngram_model.json"
        with open(model_file, "w") as f:
            json.dump(self.model.to_serializable(), f, indent=2)
        print(f" N-gram model saved to {model_file}")

        self._save_markdown_report(out)

    def _save_markdown_report(self, output_dir: Path):
        r = self.results
        report = output_dir / "STEP5_PROBABILISTIC_REPORT.md"

        with open(report, "w", encoding="utf-8") as f:
            f.write("# Step 5: Probabilistic Prediction Report (0\u2013D)\n\n")
            f.write(f"**Data source:** folders `{', '.join(TARGET_FOLDERS)}` "
                    f"under base archive.\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"- **Passwords Trained On**: {r['total_passwords_trained']:,}\n")
            f.write(f"- **Passwords Evaluated**: {r['total_passwords_evaluated']:,}\n")
            f.write(f"- **Total Characters Processed**: {r['total_chars']:,}\n")
            f.write(f"- **Unique Characters**: {r['unique_chars']:,}\n")
            st = r["predictability_stats"]
            f.write(f"- **Mean Predictability Score**: {st['mean']:.4f}\n")
            f.write(f"- **Median Predictability Score**: {st['median']:.4f}\n")
            f.write(f"- **10th / 90th Percentile**: {st['p10']:.4f} / {st['p90']:.4f}\n\n")

            f.write("## Methodology\n\n")
            f.write("A character-level n-gram language model captures how likely "
                    "each character is given the previous one(s):\n\n")
            f.write("1. **Bigram**: P(c_n | c_{n-1})\n")
            f.write("2. **Trigram**: P(c_n | c_{n-2}, c_{n-1})\n")
            f.write("3. **Interpolated**: 0.4 \u00d7 P_bigram + 0.6 \u00d7 P_trigram\n")
            f.write("4. **Laplace smoothing** handles unseen transitions\n")
            f.write("5. Predictability score scaled 0\u2013100 from average "
                    "log\u2082-probability per transition\n\n")

            f.write("## Predictability Score Distribution\n\n")
            f.write("| Score Range | Count | % |\n")
            f.write("|-------------|-------|---|\n")
            te = r["total_passwords_evaluated"]
            for bkt, cnt in sorted(r["score_distribution"].items()):
                pct = cnt / te * 100 if te else 0
                f.write(f"| {bkt}\u2013{bkt + 10} | {cnt:,} | {pct:.2f}% |\n")
            f.write("\n")

            f.write("## Top 20 Character Frequencies\n\n")
            f.write("| Rank | Char | Count | % |\n")
            f.write("|------|------|-------|---|\n")
            for i, item in enumerate(r["top_char_frequencies"][:20], 1):
                c = item["char"]
                d = c if c.isprintable() else repr(c)
                f.write(f"| {i} | `{d}` | {item['count']:,} | "
                        f"{item['percentage']:.3f}% |\n")
            f.write("\n")

            f.write("## Top 20 Most Common Transitions\n\n")
            f.write("| From | To | Count | P |\n")
            f.write("|------|----|-------|---|\n")
            for t in r["top_transitions_by_count"][:20]:
                f.write(f"| `{t['from']}` | `{t['to']}` | "
                        f"{t['count']:,} | {t['probability']:.4f} |\n")
            f.write("\n")

            f.write("## Top 20 Highest Probability Transitions\n\n")
            f.write("Given the preceding character, these next characters "
                    "are most predictable (min 1 000 occurrences).\n\n")
            f.write("| From | To | P | Count |\n")
            f.write("|------|----|---|-------|\n")
            for t in r["highest_probability_transitions"][:20]:
                f.write(f"| `{t['from']}` | `{t['to']}` | "
                        f"{t['probability']:.4f} | {t['count']:,} |\n")
            f.write("\n")

            f.write("## Sample Passwords with Scores\n\n")
            f.write("| Password | Bigram Log-P | Trigram Log-P | Predictability |\n")
            f.write("|----------|-------------|---------------|----------------|\n")
            for s in r["sample_passwords_graded"][:20]:
                f.write(f"| `{s['password']}` | {s['bigram_avg_log_prob']:.4f} | "
                        f"{s['trigram_avg_log_prob']:.4f} | "
                        f"{s['predictability']:.2f} |\n")
            f.write("\n")

            f.write("## Password Length Distribution (Top 30)\n\n")
            f.write("| Length | Count |\n")
            f.write("|--------|-------|\n")
            for length, count in sorted(
                r["password_length_distribution"].items(),
                key=lambda x: int(x[0]),
            )[:30]:
                f.write(f"| {length} | {count:,} |\n")
            f.write("\n")

        print(f" Report saved to {report}")


# ====================================================================== #
#  CLI                                                                     #
# ====================================================================== #
def parse_args():
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Step 5: Probabilistic Prediction \u2014 Character N-gram Model"
    )
    parser.add_argument(
        "--base-dir",
        default=str(script_dir.parent.parent / "Data"),
        help="Base directory containing password files (default: Data/)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Limit training to N passwords (for testing)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(script_dir),
        help="Output directory for results (default: 0-D/Phase2 folder)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    base_dir = Path(args.base_dir)

    if not base_dir.exists():
        print(f" Error: Base directory not found: {base_dir}")
        return

    analyzer = ProbabilisticPredictionAnalyzer(base_dir)
    analyzer.analyze(sample_size=args.sample)
    analyzer.save_results(args.output_dir)


if __name__ == "__main__":
    main()
