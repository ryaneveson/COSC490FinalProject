"""
Step 2: General Analysis
Identifying common passwords, common lengths, and variability of these parameters
"""

import os
import json
from collections import defaultdict, Counter
from pathlib import Path
import statistics

class PasswordGeneralAnalysis:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.file_categories = ['P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'Symbols']
        self.results = {
            'total_passwords': 0,
            'unique_passwords': 0,
            'password_counts': {},
            'top_passwords': {},
            'length_distribution': {},
            'length_stats': {},
            'variability_metrics': {},
            'category_stats': {}
        }
        
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
    
    def _calculate_median(self, counter_dict):
        """Calculate median from a counter dictionary"""
        total = sum(counter_dict.values())
        cumsum = 0
        for key in sorted(counter_dict.keys()):
            cumsum += counter_dict[key]
            if cumsum >= total / 2:
                return key
        return max(counter_dict.keys())
    
    def analyze_passwords(self, passwords):
        """Perform general analysis on passwords"""
        print("\n=== Step 2: General Analysis ===\n")
        
        # Basic counts
        self.results['total_passwords'] = len(passwords)
        print(f"Total passwords loaded: {self.results['total_passwords']:,}")
        
        # Count frequency of each password - do this only once
        print("Counting password frequencies... (this may take a while)")
        password_counter = Counter(passwords)
        self.results['unique_passwords'] = len(password_counter)
        
        print(f"Unique passwords: {self.results['unique_passwords']:,}")
        print(f"Duplicate passwords: {self.results['total_passwords'] - self.results['unique_passwords']:,}")
        
        # Get top 50 most common passwords
        top_50 = password_counter.most_common(50)
        self.results['top_passwords'] = {password: count for password, count in top_50}
        
        print(f"\nTop 20 Most Common Passwords:")
        print("-" * 60)
        for i, (password, count) in enumerate(top_50[:20], 1):
            percentage = (count / self.results['total_passwords']) * 100
            print(f"{i:2d}. '{password}' - {count:8,} times ({percentage:6.2f}%)")
        
        # Analyze password lengths while building counter
        print(f"\n=== Password Length Analysis ===\n")
        print("Analyzing password lengths...")
        
        length_counter = Counter()
        char_stats = {
            'with_digits': 0,
            'with_uppercase': 0,
            'with_lowercase': 0,
            'with_special_chars': 0
        }
        
        # Process passwords once, collecting all metrics
        for pwd, count in password_counter.items():
            length_counter[len(pwd)] += count
            
            # Check for character types
            if any(c.isdigit() for c in pwd):
                char_stats['with_digits'] += count
            if any(c.isupper() for c in pwd):
                char_stats['with_uppercase'] += count
            if any(c.islower() for c in pwd):
                char_stats['with_lowercase'] += count
            if any(not c.isalnum() for c in pwd):
                char_stats['with_special_chars'] += count
        
        self.results['length_distribution'] = dict(sorted(length_counter.items()))
        
        length_stats = {
            'min': min(length_counter.keys()),
            'max': max(length_counter.keys()),
            'mean': sum(l * c for l, c in length_counter.items()) / sum(length_counter.values()),
            'median': self._calculate_median(length_counter)
        }
        self.results['length_stats'] = length_stats
        
        print(f"Length Statistics (across {len(length_counter):,} different lengths):")
        print(f"  Min:     {length_stats['min']}")
        print(f"  Max:     {length_stats['max']}")
        print(f"  Mean:    {length_stats['mean']:.2f}")
        print(f"  Median:  {length_stats['median']:.2f}")
        
        # Distribution of lengths
        print(f"\nPassword Length Distribution (Top 20):")
        print("-" * 50)
        for length in sorted(length_counter.keys())[:20]:
            count = length_counter[length]
            percentage = (count / self.results['total_passwords']) * 100
            bar = '█' * int(percentage / 2)
            print(f"  Length {length:2d}: {count:8,} ({percentage:5.2f}%) {bar}")
        
        # Variability metrics
        print(f"\n=== Variability Metrics ===\n")
        
        self.results['variability_metrics'] = {
            'with_digits': {
                'count': char_stats['with_digits'],
                'percentage': (char_stats['with_digits'] / self.results['total_passwords']) * 100
            },
            'with_uppercase': {
                'count': char_stats['with_uppercase'],
                'percentage': (char_stats['with_uppercase'] / self.results['total_passwords']) * 100
            },
            'with_lowercase': {
                'count': char_stats['with_lowercase'],
                'percentage': (char_stats['with_lowercase'] / self.results['total_passwords']) * 100
            },
            'with_special_chars': {
                'count': char_stats['with_special_chars'],
                'percentage': (char_stats['with_special_chars'] / self.results['total_passwords']) * 100
            }
        }
        
        print(f"Passwords containing digits:      {char_stats['with_digits']:8,} ({(char_stats['with_digits'] / self.results['total_passwords']) * 100:6.2f}%)")
        print(f"Passwords containing uppercase:   {char_stats['with_uppercase']:8,} ({(char_stats['with_uppercase'] / self.results['total_passwords']) * 100:6.2f}%)")
        print(f"Passwords containing lowercase:   {char_stats['with_lowercase']:8,} ({(char_stats['with_lowercase'] / self.results['total_passwords']) * 100:6.2f}%)")
        print(f"Passwords containing special:     {char_stats['with_special_chars']:8,} ({(char_stats['with_special_chars'] / self.results['total_passwords']) * 100:6.2f}%)")
        
        # Category-specific stats
        print(f"\n=== Statistics by File Category ===\n")
        self._analyze_by_category(password_counter)
        
    def _analyze_by_category(self, password_counter):
        """Analyze statistics per category (P-Z, Symbols)"""
        
        for category in self.file_categories:
            file_path = os.path.join(self.data_dir, category, f'{category}.txt')
            if not os.path.exists(file_path):
                continue
            
            try:
                cat_password_counter = Counter()
                print(f"Processing {category}...")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        pwd = line.strip()
                        if pwd:
                            cat_password_counter[pwd] += 1
                
                total_cat = sum(cat_password_counter.values())
                unique_cat = len(cat_password_counter)
                
                lengths_cat = sum(len(pwd) * count for pwd, count in cat_password_counter.items())
                avg_length = lengths_cat / total_cat if total_cat > 0 else 0
                
                top_pwd = cat_password_counter.most_common(1)[0][0] if cat_password_counter else 'N/A'
                
                self.results['category_stats'][category] = {
                    'total': total_cat,
                    'unique': unique_cat,
                    'duplicates': total_cat - unique_cat,
                    'avg_length': avg_length,
                    'top_password': top_pwd
                }
                
                print(f"{category:10s} - Total: {total_cat:8,} | Unique: {unique_cat:8,} | Avg Length: {avg_length:6.2f}")
            except Exception as e:
                print(f"Error analyzing {category}: {e}")
    
    def save_results(self, output_dir='phase1_analysis'):
        """Save analysis results to JSON file"""
        output_file = os.path.join(output_dir, 'step2_results.json')
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert results to JSON-serializable format
        json_results = {
            'total_passwords': self.results['total_passwords'],
            'unique_passwords': self.results['unique_passwords'],
            'top_passwords': self.results['top_passwords'],
            'length_stats': self.results['length_stats'],
            'variability_metrics': self.results['variability_metrics'],
            'category_stats': self.results['category_stats']
        }
        
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n✓ Results saved to {output_file}")
        return output_file


def main():
    # Adjust path to data directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, 'data', 'archive')
    
    analyzer = PasswordGeneralAnalysis(data_dir)
    passwords = analyzer.load_passwords()
    analyzer.analyze_passwords(passwords)
    analyzer.save_results(os.path.dirname(os.path.abspath(__file__)))


if __name__ == '__main__':
    main()
