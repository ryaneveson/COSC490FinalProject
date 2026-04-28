#!/usr/bin/env python3
"""Step 9 final analysis for summarizing attack results and reports."""

import argparse
import json
import sys
from typing import Dict, List, Optional, Any
from collections import defaultdict
from pathlib import Path


def load_json(filepath: str) -> Dict:
    """Load and parse JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_by_length(results: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """Analyze crack rate by password length buckets."""
    buckets: Dict[str, Dict[str, Any]] = {
        "<8": {"cracked": 0, "total": 0},
        "8-11": {"cracked": 0, "total": 0},
        "12-15": {"cracked": 0, "total": 0},
        "16+": {"cracked": 0, "total": 0}
    }

    for result in results:
        pwd_len = len(result['target'])

        if pwd_len < 8:
            bucket = "<8"
        elif pwd_len <= 11:
            bucket = "8-11"
        elif pwd_len <= 15:
            bucket = "12-15"
        else:
            bucket = "16+"

        buckets[bucket]['total'] += 1
        if result.get('cracked', False):
            buckets[bucket]['cracked'] += 1

    # Calculate rates
    for bucket in buckets:
        total = buckets[bucket]['total']
        if total > 0:
            buckets[bucket]['rate'] = buckets[bucket]['cracked'] / total
        else:
            buckets[bucket]['rate'] = 0.0

    return buckets


def analyze_by_grade(results: List[Dict], grades_data: Optional[Dict]) -> Optional[Dict[str, Dict[str, Any]]]:
    """Analyze crack rate by grade (A, B, C, D, F)."""
    if not grades_data:
        return None

    grade_buckets: Dict[str, Dict[str, Any]] = {
        grade: {"cracked": 0, "total": 0} for grade in ['A', 'B', 'C', 'D', 'F']
    }

    # Build password to grade mapping
    pwd_to_grade = {}
    for entry in grades_data.get('grades', []):
        pwd_to_grade[entry['password']] = entry['grade']

    for result in results:
        pwd = result['target']
        grade = pwd_to_grade.get(pwd)

        if grade in grade_buckets:
            grade_buckets[grade]['total'] += 1
            if result.get('cracked', False):
                grade_buckets[grade]['cracked'] += 1

    # Calculate rates
    for grade in grade_buckets:
        total = grade_buckets[grade]['total']
        if total > 0:
            grade_buckets[grade]['rate'] = grade_buckets[grade]['cracked'] / total
        else:
            grade_buckets[grade]['rate'] = 0.0

    return grade_buckets


def analyze_by_pattern(results: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """Analyze crack rate by pattern type."""
    pattern_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"cracked": 0, "total": 0})

    for result in results:
        if result.get('cracked', False):
            pattern = result.get('cracked_by_pattern_type', 'unknown')
            pattern_stats[pattern]['cracked'] += 1
            pattern_stats[pattern]['total'] += 1
        else:
            pattern_stats['not_cracked']['total'] += 1

    # Calculate rates
    for pattern in pattern_stats:
        total = pattern_stats[pattern]['total']
        if total > 0:
            pattern_stats[pattern]['rate'] = pattern_stats[pattern]['cracked'] / total
        else:
            pattern_stats[pattern]['rate'] = 0.0

    return dict(pattern_stats)


def analyze_attempts(results: List[Dict]) -> Dict[str, Any]:
    """Analyze attempt distribution (min, max, median, mean)."""
    attempts = [r['attempts'] for r in results]

    if not attempts:
        return {"min": 0, "max": 0, "median": 0, "mean": 0.0}

    attempts_sorted = sorted(attempts)
    n = len(attempts_sorted)

    median = attempts_sorted[n // 2] if n % 2 == 1 else (attempts_sorted[n // 2 - 1] + attempts_sorted[n // 2]) / 2

    return {
        "min": min(attempts),
        "max": max(attempts),
        "median": median,
        "mean": sum(attempts) / len(attempts)
    }


def validate_grading(results: List[Dict], grades_data: Optional[Dict]) -> Optional[Dict[str, Any]]:
    """Validate grading by comparing grades vs actual crack success."""
    if not grades_data:
        return None

    pwd_to_grade = {}
    for entry in grades_data.get('grades', []):
        pwd_to_grade[entry['password']] = entry['grade']

    validation = {
        "total_graded": len(pwd_to_grade),
        "mismatches": [],
        "grade_accuracy": {}
    }

    # Expected: A/B should rarely crack, D/F should often crack
    for result in results:
        pwd = result['target']
        grade = pwd_to_grade.get(pwd)
        cracked = result.get('cracked', False)

        if grade:
            # Unexpected if high grade (A/B) cracked or low grade (D/F) not cracked
            if (grade in ['A', 'B'] and cracked) or (grade in ['D', 'F'] and not cracked):
                validation['mismatches'].append({
                    "password": pwd,
                    "grade": grade,
                    "cracked": cracked,
                    "attempts": result['attempts']
                })

    return validation


def print_console_summary(analysis: Dict):
    """Print key findings to console."""
    print("\n" + "=" * 60)
    print("PASSWORD ATTACK ANALYSIS SUMMARY")
    print("=" * 60 + "\n")

    # Overall stats
    total = analysis['overall']['total_passwords']
    cracked = analysis['overall']['cracked']
    rate = analysis['overall']['crack_rate']
    print(f"Overall Results:")
    print(f"  Total passwords: {total}")
    print(f"  Cracked: {cracked} ({rate:.1%})")
    print(f"  Not cracked: {total - cracked} ({(1 - rate):.1%})\n")

    # By length
    print("Crack Rate by Password Length:")
    for bucket, stats in analysis['by_length'].items():
        if stats['total'] > 0:
            print(f"  {bucket:6s}: {stats['cracked']:3d}/{stats['total']:3d} ({stats['rate']:.1%})")
    print()

    # By grade
    if analysis['by_grade']:
        print("Crack Rate by Grade:")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            stats = analysis['by_grade'][grade]
            if stats['total'] > 0:
                print(f"  Grade {grade}: {stats['cracked']:3d}/{stats['total']:3d} ({stats['rate']:.1%})")
        print()

    # By pattern
    print("Passwords Cracked by Pattern Type:")
    pattern_items = sorted(analysis['by_pattern'].items(), key=lambda x: x[1]['cracked'], reverse=True)
    for pattern, stats in pattern_items:
        if pattern != 'not_cracked' and stats['cracked'] > 0:
            print(f"  {pattern:20s}: {stats['cracked']:3d} cracked")
    print()

    # Attempts
    attempts = analysis['attempt_stats']
    print("Attack Attempt Statistics:")
    print(f"  Min:    {attempts['min']:8.0f}")
    print(f"  Max:    {attempts['max']:8.0f}")
    print(f"  Mean:   {attempts['mean']:8.1f}")
    print(f"  Median: {attempts['median']:8.1f}")
    print()

    print("=" * 60 + "\n")


def generate_markdown(analysis: Dict) -> str:
    """Generate formatted markdown report with tables."""
    md = []

    md.append("# Password Attack Analysis Report\n")

    # Overall stats
    md.append("## Overall Results\n")
    total = analysis['overall']['total_passwords']
    cracked = analysis['overall']['cracked']
    rate = analysis['overall']['crack_rate']
    md.append(f"- **Total passwords**: {total}")
    md.append(f"- **Cracked**: {cracked} ({rate:.1%})")
    md.append(f"- **Not cracked**: {total - cracked} ({(1 - rate):.1%})\n")

    # By length table
    md.append("## Crack Rate by Password Length\n")
    md.append("| Length Range | Cracked | Total | Rate |")
    md.append("|--------------|---------|-------|------|")
    for bucket, stats in analysis['by_length'].items():
        if stats['total'] > 0:
            md.append(f"| {bucket:12s} | {stats['cracked']:7d} | {stats['total']:5d} | {stats['rate']:5.1%} |")
    md.append("")

    # By grade table
    if analysis['by_grade']:
        md.append("## Crack Rate by Grade\n")
        md.append("| Grade | Cracked | Total | Rate |")
        md.append("|-------|---------|-------|------|")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            stats = analysis['by_grade'][grade]
            if stats['total'] > 0:
                md.append(f"| {grade:5s} | {stats['cracked']:7d} | {stats['total']:5d} | {stats['rate']:5.1%} |")
        md.append("")

    # By pattern table
    md.append("## Passwords Cracked by Pattern Type\n")
    md.append("| Pattern Type | Count |")
    md.append("|--------------|-------|")
    pattern_items = sorted(analysis['by_pattern'].items(), key=lambda x: x[1]['cracked'], reverse=True)
    for pattern, stats in pattern_items:
        if pattern != 'not_cracked' and stats['cracked'] > 0:
            md.append(f"| {pattern:20s} | {stats['cracked']:5d} |")
    md.append("")

    # Attempts stats
    md.append("## Attack Attempt Statistics\n")
    attempts = analysis['attempt_stats']
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Min    | {attempts['min']:8.0f} |")
    md.append(f"| Max    | {attempts['max']:8.0f} |")
    md.append(f"| Mean   | {attempts['mean']:8.1f} |")
    md.append(f"| Median | {attempts['median']:8.1f} |")
    md.append("")

    # Validation
    if analysis['validation']:
        val = analysis['validation']
        md.append("## Grading Validation\n")
        md.append(f"- **Total graded passwords**: {val['total_graded']}")
        md.append(f"- **Unexpected results**: {len(val['mismatches'])}\n")

        if val['mismatches']:
            md.append("### Unexpected Results\n")
            md.append("| Password | Grade | Cracked | Attempts |")
            md.append("|----------|-------|---------|----------|")
            for m in val['mismatches'][:10]:  # Limit to 10
                md.append(f"| {m['password']:8s} | {m['grade']:5s} | {m['cracked']!s:7s} | {m['attempts']:8d} |")
            md.append("")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze password attack results and generate reports"
    )
    parser.add_argument(
        '--attack-results',
        required=True,
        help='Path to JSON file with attack results (from step8)'
    )
    parser.add_argument(
        '--grades-file',
        help='Path to JSON file with password grades (from step6, optional)'
    )
    parser.add_argument(
        '--json-output',
        help='Path to output full analysis as JSON'
    )
    parser.add_argument(
        '--markdown-output',
        help='Path to output formatted markdown report'
    )

    args = parser.parse_args()

    # Load input data
    attack_data = load_json(args.attack_results)
    results = attack_data.get('results', [])

    grades_data = None
    if args.grades_file:
        grades_data = load_json(args.grades_file)

    # Perform analyses
    analysis = {
        "overall": {
            "total_passwords": len(results),
            "cracked": sum(1 for r in results if r.get('cracked', False)),
            "crack_rate": 0.0
        },
        "by_length": analyze_by_length(results),
        "by_grade": analyze_by_grade(results, grades_data),
        "by_pattern": analyze_by_pattern(results),
        "attempt_stats": analyze_attempts(results),
        "validation": validate_grading(results, grades_data)
    }

    # Calculate overall crack rate
    if analysis['overall']['total_passwords'] > 0:
        analysis['overall']['crack_rate'] = analysis['overall']['cracked'] / analysis['overall']['total_passwords']

    # Output console summary
    print_console_summary(analysis)

    # Output JSON
    if args.json_output:
        with open(args.json_output, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"Full analysis saved to: {args.json_output}")

    # Output markdown
    if args.markdown_output:
        markdown = generate_markdown(analysis)
        with open(args.markdown_output, 'w') as f:
            f.write(markdown)
        print(f"Markdown report saved to: {args.markdown_output}")


if __name__ == '__main__':
    main()
