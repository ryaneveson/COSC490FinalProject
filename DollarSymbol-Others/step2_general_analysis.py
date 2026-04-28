import argparse
import math
from collections import Counter
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


def is_lfs_pointer(file_path: Path) -> bool:
    # Detect Git LFS placeholder files so we do not treat metadata as passwords.
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


def run_step2(base_dir: Path, top_n: int):
    length_counts = Counter()
    total = 0

    for password in iter_passwords(base_dir):
        total += 1
        length_counts[len(password)] += 1

    print("\n=== STEP 2: GENERAL ANALYSIS (DollarSymbol -> Others) ===")
    print(f"Target folders: {', '.join(TARGET_FOLDERS)}")
    print(f"Total passwords processed: {total:,}")

    if not length_counts:
        print("No passwords processed. If you expected data, run `git lfs pull` first.")
        return

    # Expand counts into a per-password length list for mean/variance math.
    lengths_expanded = list(length_counts.elements())
    mean_len = sum(lengths_expanded) / total
    variance = sum((x - mean_len) ** 2 for x in lengths_expanded) / total
    std_dev = math.sqrt(variance)

    print(f"Length mean: {mean_len:.2f}")
    print(f"Length std dev: {std_dev:.2f}")
    print(f"Length min: {min(length_counts)}")
    print(f"Length max: {max(length_counts)}")

    print(f"\nTop {top_n} most common lengths:")
    for length, count in length_counts.most_common(top_n):
        print(f"- length {length}: {count:,}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Step 2 general password analysis for folders DollarSymbol through Others"
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
        help="Top N lengths to print (default: 20)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_step2(Path(args.base_dir), args.top)


if __name__ == "__main__":
    main()
