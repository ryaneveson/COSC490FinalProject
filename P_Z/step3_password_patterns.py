"""
Step 3: Password Pattern Analysis
Convert passwords to masks and analyze masking patterns
Masks: C (Capital), L (lowercase), D (digit), S (special character)
"""

import os
import json
import re
from collections import defaultdict, Counter
from pathlib import Path
import statistics


class PasswordMaskAnalyzer:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.file_categories = ['P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'Symbols']
        self.results = {
            'total_masks': 0,
            'unique_masks': 0,
            'mask_counts': {},
            'top_masks': {},
            'mask_length_distribution': {},
            'pattern_complexity_stats': {},
            'character_set_patterns': {}
        }
    
    def password_to_mask(self, password):
        """
        Convert a password to its mask representation
        C = uppercase letter
        L = lowercase letter
        D = digit
        S = special character
        """
        mask = ""
        for char in password:
            if char.isupper():
                mask += "C"
            elif char.islower():
                mask += "L"
            elif char.isdigit():
                mask += "D"
            else:  # Special character
                mask += "S"
        return mask
    
    def load_passwords(self):
        """Load all passwords from files P-Z and Symbols"""
        all_passwords = []
        
        for category in self.file_categories:
            file_path = os.path.join(self.data_dir, category, f'{category}.txt')
            
            if not os.path.exists(file_path):
                print(f"Warning: {file_path} not found")
                continue
            
            print(f"Loading passwords from {category}...")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    passwords = [line.strip() for line in f if line.strip()]
                    all_passwords.extend(passwords)
                    print(f"  - Loaded {len(passwords)} passwords from {category}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return all_passwords
    
    def analyze_patterns(self, passwords):
        """Perform pattern analysis on passwords"""
        print("\n=== Step 3: Password Pattern Analysis ===\n")
        
        # Convert all passwords to masks - use a counter to track with frequencies
        print("Converting passwords to masks and analyzing patterns... this may take a while")
        
        mask_counter = Counter()
        charset_counter = Counter()
        complexity_counter = Counter()
        
        for pwd in passwords:
            mask = self.password_to_mask(pwd)
            mask_counter[mask] += 1
            
            # Get character sets present
            charsets = []
            if any(c.isupper() for c in pwd):
                charsets.append('C')
            if any(c.islower() for c in pwd):
                charsets.append('L')
            if any(c.isdigit() for c in pwd):
                charsets.append('D')
            if any(not c.isalnum() for c in pwd):
                charsets.append('S')
            
            charset_combo = ''.join(sorted(charsets))
            charset_counter[charset_combo] += 1
            complexity_counter[len(charsets)] += 1
        
        self.results['total_masks'] = len(passwords)
        unique_masks = len(mask_counter)
        self.results['unique_masks'] = unique_masks
        
        print(f"Total passwords analyzed: {len(passwords):,}")
        print(f"Total masks (all combinations): {len(passwords):,}")
        print(f"Unique masks: {unique_masks:,}")
        
        # Get top masks
        top_100 = mask_counter.most_common(100)
        self.results['top_masks'] = {mask: count for mask, count in top_100}
        
        print(f"\n=== Top 30 Most Frequent Password Masks ===\n")
        print("-" * 80)
        print(f"{'Rank':<5} {'Mask':<30} {'Count':<12} {'Percentage':<12}")
        print("-" * 80)
        
        for i, (mask, count) in enumerate(top_100[:30], 1):
            percentage = (count / len(passwords)) * 100
            # Format mask with spaces for readability
            mask_formatted = ' '.join(mask)
            print(f"{i:<5} {mask_formatted:<30} {count:<12,} {percentage:<12.2f}%")
        
        # Analyze mask lengths
        print(f"\n=== Password Length vs Mask Distribution ===\n")
        mask_length_counter = Counter(len(mask) for mask in mask_counter.keys())
        self.results['mask_length_distribution'] = dict(sorted(mask_length_counter.items()))
        
        print(f"Length Distribution (Top 15):")
        print("-" * 50)
        for length in sorted(mask_length_counter.keys())[:15]:
            count = mask_length_counter[length]
            percentage = (count / len(mask_counter)) * 100
            bar = '█' * int(percentage / 3)
            print(f"  Length {length:2d}: {count:6,} masks ({percentage:5.2f}%) {bar}")
        
        # Analyze pattern complexity
        print(f"\n=== Pattern Complexity Analysis ===\n")
        self._analyze_complexity_from_counter(complexity_counter, len(passwords))
        
        # Analyze character set patterns
        print(f"\n=== Character Set Combination Patterns ===\n")
        self._analyze_character_sets_from_counter(charset_counter)
    
    def _analyze_complexity_from_counter(self, complexity_counter, total):
        """Analyze complexity of patterns from pre-computed counter"""
        
        complexity_names = {
            1: "Only 1 character set",
            2: "2 character sets",
            3: "3 character sets",
            4: "All 4 character sets"
        }
        
        print("Complexity Distribution (by character set diversity):")
        print("-" * 60)
        for level in sorted(complexity_counter.keys()):
            count = complexity_counter[level]
            percentage = (count / total) * 100
            name = complexity_names.get(level, f"Level {level}")
            bar = '█' * int(percentage / 2)
            print(f"{name:30s}: {count:10,} ({percentage:6.2f}%) {bar}")
        
        self.results['pattern_complexity_stats'] = {
            f'level_{level}': {
                'count': complexity_counter.get(level, 0),
                'percentage': (complexity_counter.get(level, 0) / total) * 100
            }
            for level in range(1, 5)
        }
    
    def _analyze_complexity(self, all_masks, unique_masks):
        """Analyze complexity of patterns"""
        def get_complexity_level(mask):
            """Determine complexity level based on character set diversity"""
            has_upper = 'C' in mask
            has_lower = 'L' in mask
            has_digit = 'D' in mask
            has_special = 'S' in mask
            
            diversity = sum([has_upper, has_lower, has_digit, has_special])
            return diversity
        
        complexity_counter = Counter(get_complexity_level(mask) for mask in all_masks)
        complexity_names = {
            1: "Only 1 character set",
            2: "2 character sets",
            3: "3 character sets",
            4: "All 4 character sets"
        }
        
        print("Complexity Distribution (by character set diversity):")
        print("-" * 60)
        total = sum(complexity_counter.values())
        for level in sorted(complexity_counter.keys()):
            count = complexity_counter[level]
            percentage = (count / total) * 100
            name = complexity_names.get(level, f"Level {level}")
            bar = '█' * int(percentage / 2)
            print(f"{name:30s}: {count:10,} ({percentage:6.2f}%) {bar}")
        
        self.results['pattern_complexity_stats'] = {
            f'level_{level}': {
                'count': complexity_counter.get(level, 0),
                'percentage': (complexity_counter.get(level, 0) / total) * 100
            }
            for level in range(1, 5)
        }
    
    def _analyze_character_sets_from_counter(self, charset_counter):
        """Analyze which character set combinations are most common from counter"""
        
        charset_names = {
            'C': 'Uppercase only',
            'L': 'Lowercase only',
            'D': 'Digits only',
            'S': 'Special chars only',
            'CD': 'Uppercase + Digits',
            'CL': 'Uppercase + Lowercase',
            'CS': 'Uppercase + Special',
            'CLD': 'Upper + Lower + Digit',
            'CLS': 'Upper + Lower + Special',
            'CDS': 'Upper + Digit + Special',
            'LD': 'Lower + Digits',
            'LS': 'Lower + Special',
            'LDS': 'Lower + Digit + Special',
            'DS': 'Digit + Special',
            'CLDS': 'All 4 character sets'
        }
        
        print("Character Set Combinations:")
        print("-" * 70)
        print(f"{'Combination':<30} {'Count':<12} {'Percentage':<15}")
        print("-" * 70)
        
        total_count = sum(charset_counter.values())
        for charset, count in charset_counter.most_common():
            percentage = (count / total_count) * 100
            name = charset_names.get(charset, charset)
            print(f"{name:<30} {count:<12,} {percentage:<15.2f}%")
        
        self.results['character_set_patterns'] = {
            charset_names.get(charset, charset): {
                'count': count,
                'percentage': (count / total_count) * 100
            }
            for charset, count in charset_counter.most_common()
        }
    
    def _analyze_character_sets(self, passwords, unique_masks):
        """Placeholder - actual analysis is done in _analyze_character_sets_from_counter"""
        pass
    
    def save_results(self, output_dir='phase1_analysis'):
        """Save analysis results to JSON file"""
        output_file = os.path.join(output_dir, 'step3_results.json')
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert results to JSON-serializable format
        json_results = {
            'total_masks': self.results['total_masks'],
            'unique_masks': self.results['unique_masks'],
            'top_masks': dict(list(self.results['top_masks'].items())[:50]),  # Save top 50
            'mask_length_distribution': self.results['mask_length_distribution'],
            'pattern_complexity_stats': self.results['pattern_complexity_stats'],
            'character_set_patterns': self.results['character_set_patterns']
        }
        
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n✓ Results saved to {output_file}")
        
        # Also create a visualization of top masks
        self._save_mask_visualization(output_dir, self.results['top_masks'])
        
        return output_file
    
    def _save_mask_visualization(self, output_dir, top_masks):
        """Save a readable version of top masks"""
        output_file = os.path.join(output_dir, 'step3_top_masks.txt')
        
        with open(output_file, 'w') as f:
            f.write("=== Top 50 Password Masks ===\n\n")
            f.write("Legend: C=Capital, L=lowercase, D=Digit, S=Special\n\n")
            f.write(f"{'Rank':<5} {'Mask':<40} {'Count':<12} {'Percentage':<12}\n")
            f.write("-" * 80 + "\n")
            
            for i, (mask, count) in enumerate(list(top_masks.items())[:50], 1):
                mask_formatted = ' '.join(mask)
                percentage = (count / sum(top_masks.values())) * 100
                f.write(f"{i:<5} {mask_formatted:<40} {count:<12,} {percentage:<12.2f}%\n")
        
        print(f"✓ Mask visualization saved to {output_file}")


def main():
    # Adjust path to data directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, 'data', 'archive')
    
    analyzer = PasswordMaskAnalyzer(data_dir)
    passwords = analyzer.load_passwords()
    analyzer.analyze_patterns(passwords)
    analyzer.save_results(os.path.dirname(os.path.abspath(__file__)))


if __name__ == '__main__':
    main()
