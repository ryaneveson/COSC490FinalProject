import argparse
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


def char_to_mask(char: str) -> str:
    if char.isupper():
        return "C"
    if char.islower():
        return "L"
    if char.isdigit():
        return "D"
    # Everything not letter/digit is treated as a special character.
    return "S"


def password_to_mask(password: str) -> str:
    # Keep spaces between mask symbols for easier human scanning in reports.
    return " ".join(char_to_mask(char) for char in password)


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


def run_step3(base_dir: Path, top_n: int):
    mask_counts = Counter()
    total = 0

    for password in iter_passwords(base_dir):
        total += 1
        mask_counts[password_to_mask(password)] += 1

    print("\n=== STEP 3: PASSWORD MASK PATTERNS (DollarSymbol -> Others) ===")
    print("Mask key: C=Capital, L=Lower, D=Digit, S=Special")
    print(f"Target folders: {', '.join(TARGET_FOLDERS)}")
    print(f"Total passwords processed: {total:,}")

    if not mask_counts:
        print("No passwords processed. If you expected data, run `git lfs pull` first.")
        return

    print(f"\nTop {top_n} mask patterns:")
    for mask, count in mask_counts.most_common(top_n):
        print(f"- {count:,} -> {mask}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Step 3 mask pattern analysis for folders DollarSymbol through Others"
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
        help="Top N mask patterns to print (default: 20)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_step3(Path(args.base_dir), args.top)


if __name__ == "__main__":
    main()
