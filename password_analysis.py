import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

# only analyze my sections of the data
ALLOWED_FOLDER_NAMES = frozenset("0123456789ABCD")

# mask each charatcter from the password 
# C = Capital
# S = Special
# L = Lower
# D = Digit
def char_to_mask(c: str) -> str:
    if len(c) != 1:
        return ""
    if c.isupper():
        return "C"
    if c.islower():
        return "L"
    if c.isdigit():
        return "D"
    return "S"


def password_to_mask(password: str) -> str:
    """convert password to mask pattern, e.g. P@ss123 -> C S L L D D D"""
    return " ".join(char_to_mask(c) for c in password)


def iter_passwords_from_folder(folder_path: str, allowed_subfolders: Optional[frozenset] = None):
    # iterate through all the .txt files in the folder
    folder = Path(folder_path)
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    allowed = allowed_subfolders or frozenset()
    if allowed:
        # only look inside the folders that are allowed
        for name in sorted(allowed):
            subdir = folder / name
            if not subdir.is_dir():
                continue
            for p in subdir.rglob("*.txt"):
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        password = line.strip()
                        if password:
                            yield password, str(p)
    else:
        for p in folder.rglob("*.txt"):
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    password = line.strip()
                    if password:
                        yield password, str(p)


def run_analysis(
    folder_path: str,
    top_n: int = 20,
    sample_cap: Optional[int] = None,
    output_dir: str = "output",
):
    # count the length of the passwords and the mask patterns
    length_counts: Counter = Counter()
    mask_counts: Counter = Counter()
    total = 0

    parent_name = Path(folder_path).name
    allowed = ALLOWED_FOLDER_NAMES if parent_name not in ALLOWED_FOLDER_NAMES else None
    for password, file_path in iter_passwords_from_folder(folder_path, allowed_subfolders=allowed):
        total += 1
        length_counts[len(password)] += 1
        mask = password_to_mask(password)
        mask_counts[mask] += 1
        if sample_cap and total >= sample_cap:
            break

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not length_counts:
        with open(out / "password_analysis_report.md", "w", encoding="utf-8") as f:
            f.write("# Password Analysis Report\n\nNo data to analyze.\n")
        return

    lengths = list(length_counts.elements())
    mean_len = sum(lengths) / len(lengths)
    variance = sum((x - mean_len) ** 2 for x in lengths) / len(lengths)
    std_dev = variance ** 0.5
    min_len = min(length_counts)
    max_len = max(length_counts)

    # --- CSV: summary ---
    summary_path = out / "password_analysis_summary.csv"
    with open(summary_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["total_passwords", total])
        w.writerow(["mean_length", f"{mean_len:.2f}"])
        w.writerow(["std_dev_length", f"{std_dev:.2f}"])
        w.writerow(["min_length", min_len])
        w.writerow(["max_length", max_len])

    # --- CSV: length counts (all) ---
    lengths_path = out / "password_analysis_lengths.csv"
    with open(lengths_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["length", "count"])
        for length, count in length_counts.most_common():
            w.writerow([length, count])

    # --- CSV: mask patterns (all) ---
    masks_path = out / "password_analysis_masks.csv"
    with open(masks_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mask", "count"])
        for mask, count in mask_counts.most_common():
            w.writerow([mask, count])

    # --- Markdown report ---
    report_lines = [
        "# Password Analysis Report",
        "",
        f"**Data folder:** `{folder_path}`",
        f"**Total passwords:** {total:,}",
        "",
        "## STEP 2: General analysis",
        "",
        f"- **Length — mean:** {mean_len:.2f}, **std dev:** {std_dev:.2f}",
        f"- **Length — min:** {min_len}, **max:** {max_len}",
        "",
        f"### Top {top_n} most common lengths (length → count)",
        "",
        "| Count | Length |",
        "|------:|-------:|",
    ]
    for length, count in length_counts.most_common(top_n):
        report_lines.append(f"| {count:,} | {length} |")

    report_lines.extend([
        "",
        "## STEP 3: Password mask patterns (C=Cap, S=Special, L=Lower, D=Digit)",
        "",
        f"### Top {top_n} most frequent mask patterns",
        "",
        "| Count | Mask |",
        "|------:|------|",
    ])
    for mask, count in mask_counts.most_common(top_n):
        report_lines.append(f"| {count:,} | {mask} |")

    report_lines.extend([
        "",
        "---",
        "",
        "**Output files:**",
        f"- `{summary_path.name}` — summary metrics",
        f"- `{lengths_path.name}` — full length counts",
        f"- `{masks_path.name}` — full mask pattern counts",
        "",
    ])

    report_path = out / "password_analysis_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))


def main():
    parser = argparse.ArgumentParser(
        description="Run password general analysis and mask-pattern analysis on a folder of .txt files."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default="data/archive",
        help="Folder containing .txt password files (default: data/archive)",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=20,
        help="Number of top items to show for common passwords, lengths, and masks (default: 20)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help="Cap: only process first N passwords (for quick tests)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output",
        metavar="DIR",
        help="Directory for CSV and markdown output (default: output)",
    )
    args = parser.parse_args()

    folder_path = os.path.abspath(args.folder)
    if not os.path.isdir(folder_path):
        print(f"Error: folder not found: {folder_path}", file=sys.stderr)
        sys.exit(1)

    run_analysis(
        folder_path,
        top_n=args.top,
        sample_cap=args.sample,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
