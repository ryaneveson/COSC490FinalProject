"""
Step 4: Semantic Decomposition
Uses external libraries for:
- Dictionary lookup (english-words library)
- POS tagging & word classification (spaCy + NLTK WordNet)
- L33t detection
- Keyboard pattern detection
- Pattern type ranking

To download the libraries, run:
# Dictionary lookup
pip install english-words

# NLP - spaCy
pip install spacy
python -m spacy download en_core_web_sm

# NLP - NLTK 
pip install nltk
"""

import os
import json
import re
import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Set, Dict, List, Tuple

# Dictionary library
try:
    from english_words import get_english_words_set
    DICT_AVAILABLE = True
except ImportError:
    DICT_AVAILABLE = False
    print("  english-words not installed. Install with: pip install english-words")

# NLP libraries
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("  spaCy not installed. Install with: pip install spacy")
    print("   Then run: python -m spacy download en_core_web_sm")

try:
    from nltk.corpus import wordnet
    from nltk import download as nltk_download
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("  NLTK not installed. Install with: pip install nltk")

# Download NLTK data if needed
if NLTK_AVAILABLE:
    try:
        wordnet.synsets('test')
    except:
        print("Downloading NLTK wordnet data...")
        nltk_download('wordnet', quiet=True)
        nltk_download('averaged_perceptron_tagger', quiet=True)
        nltk_download('punkt', quiet=True)



DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'archive', '100k-most-used-passwords-NCSC.txt')

# L33t speak replacements
LEET_REPLACEMENTS = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
    "9": "g",
    "@": "a",
    "$": "s",
    "!": "i",
    "+": "t",
}

# Keyboard patterns
KEYBOARD_ROWS = [
    "1234567890",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
]

COMMON_KEYBOARD_PATTERNS = {
    "qwerty", "asdf", "zxcv", "1234", "12345", "123456", "1234567",
    "qaz", "wsx", "edc", "rfv", "tgy", "uhy", "ijm", "poiuy",
    "asdfgh", "qwert", "12341", "qazwsx",
}


# Pre-compile keyboard patterns
KEYBOARD_PATTERNS_COMPILED = set()
if KEYBOARD_ROWS:
    for row in KEYBOARD_ROWS:
        for i in range(len(row) - 2):
            seq = row[i:i+3]
            KEYBOARD_PATTERNS_COMPILED.add(seq)
            KEYBOARD_PATTERNS_COMPILED.add(seq[::-1])

class SemanticDecompositionAnalyzer:
    def __init__(self, data_file: str):
        self.data_file = data_file
        
        # Initialize NLP components
        self.nlp = None
        self.dictionary = None
        
        # Cache for POS tagging and WordNet
        self.pos_cache = {}
        self.wordnet_cache = {}
        
        self._init_dictionary()
        self._init_nlp()
        
        # Statistics collectors
        self.results = {
            'total_passwords': 0,
            'dictionary_matches': 0,
            'leet_matches': 0,
            'keyboard_patterns': 0,
            'matched_words': {},
            'word_pos_tags': {},
            'word_categories': {},
            'leet_examples': [],
            'keyboard_examples': [],
            'pattern_types': {},
            'top_words_by_pos': {},
            'wordnet_examples': {},
        }
    
    def _init_dictionary(self):
        """Initialize dictionary lookup library"""
        if DICT_AVAILABLE:
            try:
                self.dictionary = get_english_words_set(['web2'], lower=True)
                print(f" Loaded {len(self.dictionary):,} words from english-words library")
            except Exception as e:
                print(f"  Failed to load dictionary: {e}")
                self.dictionary = None
        else:
            print("  Dictionary not available. Will not perform dictionary lookup.")
    
    def _init_nlp(self):
        """Initialize spaCy NLP model"""
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
                print(" spaCy model 'en_core_web_sm' loaded successfully")
            except OSError:
                print("  spaCy model not found. Run: python -m spacy download en_core_web_sm")
        else:
            print("  spaCy not available. Will use NLTK fallback for POS tagging.")
    
    def normalize_leet(self, text: str) -> str:
        """Normalize l33t speak substitutions"""
        return "".join(LEET_REPLACEMENTS.get(char, char) for char in text.lower())
    
    def extract_tokens(self, text: str) -> List[str]:
        """Extract alphabetic tokens from text (optimized)"""
        tokens = []
        current_token = []
        for char in text.lower():
            if char.isalpha():
                current_token.append(char)
            elif current_token:
                token = ''.join(current_token)
                if len(token) > 1:  # Skip single letters
                    tokens.append(token)
                current_token = []
        if current_token:
            token = ''.join(current_token)
            if len(token) > 1:
                tokens.append(token)
        return tokens
    
    def has_keyboard_pattern(self, password: str) -> bool:
        """Check for keyboard patterns using pre-compiled patterns"""
        p = password.lower()
        
        # Check common patterns (fast set membership)
        if any(pattern in p for pattern in COMMON_KEYBOARD_PATTERNS):
            return True
        
        # Check pre-compiled keyboard patterns (much faster)
        if any(pattern in p for pattern in KEYBOARD_PATTERNS_COMPILED):
            return True
        
        return False
    
    def get_pos_tag_spacy(self, word: str) -> str:
        """Get POS tag using spaCy"""
        if not self.nlp:
            return "UNKNOWN"
        
        doc = self.nlp(word.lower())
        if doc and len(doc) > 0:
            return doc[0].pos_
        return "UNKNOWN"
    
    def get_pos_tag_wordnet(self, word: str) -> str:
        """Get POS tag using NLTK WordNet"""
        if not NLTK_AVAILABLE:
            return "UNKNOWN"
        
        synsets = wordnet.synsets(word.lower())
        if synsets:
            return synsets[0].pos()
        return "UNKNOWN"
    
    def classify_word_pos(self, word: str) -> str:
        """
        Classify word by part of speech using available NLP libraries with caching.
        Priority: spaCy > WordNet > Unknown
        """
        word_lower = word.lower()
        
        # Check cache first
        if word_lower in self.pos_cache:
            return self.pos_cache[word_lower]
        
        pos_map = {
            'PROPN': 'proper_noun',
            'NOUN': 'noun',
            'VERB': 'verb',
            'ADJ': 'adjective',
            'ADV': 'adverb',
            'NUM': 'number',
            'ADP': 'adposition',
            'CCONJ': 'conjunction',
            'DET': 'determiner',
            'INTJ': 'interjection',
            'PRON': 'pronoun',
            'SCONJ': 'subordinating_conjunction',
        }
        
        result = 'unknown'
        
        # Try spaCy first (most accurate)
        if self.nlp:
            pos_tag = self.get_pos_tag_spacy(word_lower)
            if pos_tag in pos_map:
                result = pos_map[pos_tag]
                self.pos_cache[word_lower] = result
                return result
        
        # Fallback to WordNet
        if NLTK_AVAILABLE:
            try:
                synsets = wordnet.synsets(word_lower)
                if synsets:
                    lexname = synsets[0].lexname()
                    if 'person' in lexname:
                        result = 'proper_noun'
                    elif 'noun' in lexname:
                        result = 'noun'
                    elif 'verb' in lexname:
                        result = 'verb'
                    elif 'adj' in lexname:
                        result = 'adjective'
                    elif 'adv' in lexname:
                        result = 'adverb'
            except:
                pass
        
        self.pos_cache[word_lower] = result
        return result
    
    def get_wordnet_definition(self, word: str) -> str:
        """Get WordNet definition for a word (cached)"""
        if not NLTK_AVAILABLE:
            return ""
        
        word_lower = word.lower()
        if word_lower in self.wordnet_cache:
            return self.wordnet_cache[word_lower]
        
        result = ""
        try:
            synsets = wordnet.synsets(word_lower)
            if synsets:
                result = synsets[0].definition()
        except:
            pass
        
        self.wordnet_cache[word_lower] = result
        return result
    
    def iter_passwords(self):
        """Yield all passwords from the 100k-most-used-passwords-NCSC.txt file"""
        if not os.path.exists(self.data_file):
            print(f"Error: {self.data_file} not found")
            return
        with open(self.data_file, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                pwd = line.strip()
                if pwd:
                    yield pwd

    def analyze(self, sample_size: int = None):
        """Run semantic decomposition analysis"""
        print("\n" + "="*80)
        print("STEP 4: SEMANTIC DECOMPOSITION")
        print("="*80 + "\n")
        
        if not self.dictionary:
            print(" ERROR: Dictionary not loaded. Install with: pip install english-words")
            return
        
        total = 0
        dict_matches = 0
        leet_matches = 0
        keyboard_matches = 0
        
        matched_words_counter = Counter()
        pos_tag_counts = Counter()
        pattern_type_counter = Counter()
        leet_examples = []
        keyboard_examples = []
        words_by_pos = defaultdict(Counter)
        
        print(f"Analyzing passwords from: {os.path.basename(self.data_file)}\n")
        
        for idx, password in enumerate(self.iter_passwords()):
            if sample_size and idx >= sample_size:
                break
            
            total += 1
            if total % 100000 == 0:
                print(f"  Processed {total:,} passwords...")
            
            lowered = password.lower()
            normalized_leet = self.normalize_leet(password)
            
            # Extract tokens
            tokens_plain = set(self.extract_tokens(lowered))
            tokens_leet = set(self.extract_tokens(normalized_leet))
            
            # Dictionary matching using library
            plain_hits = tokens_plain.intersection(self.dictionary)
            leet_hits = tokens_leet.intersection(self.dictionary)
            
            if plain_hits or leet_hits:
                dict_matches += 1
                
                # Classify words by POS
                all_hits = plain_hits.union(leet_hits)
                for word in all_hits:
                    matched_words_counter[word] += 1
                    pos_tag = self.classify_word_pos(word)
                    pos_tag_counts[pos_tag] += 1
                    words_by_pos[pos_tag][word] += 1
                
                # Track leet-only hits
                if leet_hits and not plain_hits:
                    leet_matches += 1
                    if len(leet_examples) < 50:
                        leet_examples.append({
                            'password': password,
                            'leet_words': list(leet_hits),
                            'reversed': [self.normalize_leet(w) for w in leet_hits],
                        })
            
            # Keyboard pattern detection
            if self.has_keyboard_pattern(password):
                keyboard_matches += 1
                if len(keyboard_examples) < 50:
                    keyboard_examples.append(password)
            
            # Pattern type classification
            pattern_type = self._classify_pattern_type(password, tokens_plain)
            pattern_type_counter[pattern_type] += 1
        
        self.results['total_passwords'] = total
        self.results['dictionary_matches'] = dict_matches
        self.results['leet_matches'] = leet_matches
        self.results['keyboard_patterns'] = keyboard_matches
        self.results['matched_words'] = dict(matched_words_counter.most_common(100))
        self.results['word_pos_tags'] = dict(pos_tag_counts)
        self.results['leet_examples'] = leet_examples
        self.results['keyboard_examples'] = keyboard_examples
        self.results['pattern_types'] = dict(pattern_type_counter)
        
        # Get top words by POS
        for pos, words in words_by_pos.items():
            top_20 = words.most_common(20)
            self.results['top_words_by_pos'][pos] = dict(top_20)
            
            # Get definitions only for top 3 words if WordNet available (faster)
            if NLTK_AVAILABLE and top_20:
                defs = {}
                for word, _ in top_20[:3]:  # Only top 3 words
                    definition = self.get_wordnet_definition(word)
                    if definition:
                        defs[word] = definition
                if defs:
                    self.results['wordnet_examples'][pos] = defs
        
        self._print_results(total)
    
    def _classify_pattern_type(self, password: str, tokens: Set[str]) -> str:
        """Classify password pattern type"""
        has_dict_word = bool(tokens)
        has_leet = any(c in password for c in LEET_REPLACEMENTS.keys())
        has_keyboard = self.has_keyboard_pattern(password)
        has_special = any(not c.isalnum() for c in password)
        has_digits = any(c.isdigit() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        
        # Pattern classification logic
        if has_dict_word and has_special and has_digits:
            if has_upper and has_lower:
                return "word_special_digit_mixed"
            elif has_upper:
                return "word_special_digit_upper"
            else:
                return "word_special_digit_lower"
        elif has_dict_word and has_digits:
            return "word_digit"
        elif has_dict_word and has_special:
            return "word_special"
        elif has_dict_word:
            return "word_only"
        elif has_keyboard:
            return "keyboard_pattern"
        elif has_leet:
            return "leet_speak"
        elif has_special and has_digits:
            return "special_digit"
        elif has_digits:
            return "digit_only"
        else:
            return "other"
    
    def _print_results(self, total: int):
        """Print analysis results"""
        print("\n" + "="*80)
        print("SEMANTIC DECOMPOSITION RESULTS")
        print("="*80 + "\n")
        
        def pct(value: int) -> float:
            return (value / total * 100) if total > 0 else 0
        
        # Dictionary matches
        print(" DICTIONARY LOOKUP (english-words library)")
        print("-" * 80)
        print(f"Total passwords analyzed:        {total:,}")
        print(f"Passwords with dictionary words: {self.results['dictionary_matches']:,} ({pct(self.results['dictionary_matches']):.2f}%)")
        print(f"Dictionary size:                 {len(self.dictionary):,} words" if self.dictionary else "Dictionary size:                 Not loaded")
        print()
        
        # POS Classification
        print(" PART-OF-SPEECH CLASSIFICATION (spaCy + WordNet)")
        print("-" * 80)
        total_pos_matches = sum(self.results['word_pos_tags'].values())
        pos_sorted = sorted(
            self.results['word_pos_tags'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for pos, count in pos_sorted:
            percentage = (count / total_pos_matches * 100) if total_pos_matches > 0 else 0
            bar = '█' * int(percentage / 2)
            print(f"{pos:25s}: {count:8,} matches ({percentage:6.2f}%) {bar}")
        print()
        
        # Top words by POS
        print(" TOP WORDS BY PART-OF-SPEECH")
        print("-" * 80)
        for pos in sorted(self.results['top_words_by_pos'].keys()):
            top_words = self.results['top_words_by_pos'][pos]
            if top_words:
                print(f"\n{pos.upper().replace('_', ' ')}:")
                for word, count in list(top_words.items())[:10]:
                    definition = ""
                    if pos in self.results['wordnet_examples'] and word in self.results['wordnet_examples'][pos]:
                        definition = f" - {self.results['wordnet_examples'][pos][word][:50]}..."
                    print(f"  {word:20s}: {count:6,}{definition}")
        print()
        
        # L33t detection
        print("L33T SPEAK DETECTION")
        print("-" * 80)
        leet_only = self.results['leet_matches']
        print(f"Passwords with l33t-only words: {leet_only:,} ({pct(leet_only):.2f}%)")
        
        if self.results['leet_examples']:
            print(f"\nExamples (first 10):")
            for example in self.results['leet_examples'][:10]:
                print(f"  {example['password']:30s} → {', '.join(example['leet_words'])}")
        print()
        
        # Keyboard patterns
        print("  KEYBOARD PATTERN DETECTION")
        print("-" * 80)
        keyboard_count = self.results['keyboard_patterns']
        print(f"Passwords with keyboard patterns: {keyboard_count:,} ({pct(keyboard_count):.2f}%)")
        
        if self.results['keyboard_examples']:
            print(f"\nExamples (first 10):")
            for example in self.results['keyboard_examples'][:10]:
                print(f"  {example}")
        print()
        
        # Pattern type ranking
        print(" PATTERN TYPE RANKING (MOST PREDICTABLE → LEAST)")
        print("-" * 80)
        pattern_types = sorted(
            self.results['pattern_types'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        total_patterns = sum(v for _, v in pattern_types)
        cumulative = 0
        
        print(f"{'Rank':<5} {'Pattern Type':<35} {'Count':<12} {'%':<10} {'Cumulative':<12}")
        print("-" * 80)
        
        for rank, (pattern_type, count) in enumerate(pattern_types, 1):
            percentage = (count / total_patterns * 100) if total_patterns > 0 else 0
            cumulative += percentage
            print(f"{rank:<5} {pattern_type:<35} {count:<12,} {percentage:6.2f}%  {cumulative:7.2f}%")
        
        print()
        print(" TOP 20 MATCHED DICTIONARY WORDS")
        print("-" * 80)
        for word, count in list(self.results['matched_words'].items())[:20]:
            print(f"  {word:20s}: {count:6,}")
    
    def save_results(self, output_dir: str = "."):
        """Save analysis results to JSON"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        output_file = output_path / "step4_semantic_results.json"
        
        # Convert for JSON serialization
        json_results = {
            'total_passwords': self.results['total_passwords'],
            'dictionary_size': len(self.dictionary) if self.dictionary else 0,
            'dictionary_matches': self.results['dictionary_matches'],
            'dictionary_match_percentage': (
                self.results['dictionary_matches'] / self.results['total_passwords'] * 100
                if self.results['total_passwords'] > 0 else 0
            ),
            'leet_matches': self.results['leet_matches'],
            'leet_match_percentage': (
                self.results['leet_matches'] / self.results['total_passwords'] * 100
                if self.results['total_passwords'] > 0 else 0
            ),
            'keyboard_patterns': self.results['keyboard_patterns'],
            'keyboard_pattern_percentage': (
                self.results['keyboard_patterns'] / self.results['total_passwords'] * 100
                if self.results['total_passwords'] > 0 else 0
            ),
            'matched_words': self.results['matched_words'],
            'word_pos_tags': self.results['word_pos_tags'],
            'pattern_types': self.results['pattern_types'],
            'top_words_by_pos': self.results['top_words_by_pos'],
            'wordnet_definitions': self.results['wordnet_examples'],
            'leet_examples': self.results['leet_examples'][:20],  # Save first 20
            'keyboard_examples': self.results['keyboard_examples'][:20],
        }
        
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n Results saved to {output_file}")
        
        # Also save detailed markdown report
        self._save_markdown_report(output_path)
    
    def _save_markdown_report(self, output_dir: Path):
        """Save detailed markdown report"""
        report_file = output_dir / "STEP4_SEMANTIC_REPORT.md"
        
        with open(report_file, 'w') as f:
            f.write("# Step 4: Semantic Decomposition Report\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Passwords Analyzed**: {self.results['total_passwords']:,}\n")
            dict_info = f"english-words library ({len(self.dictionary):,} words)" if self.dictionary else "english-words library (not loaded)"
            f.write(f"- **Dictionary Used**: {dict_info}\n")
            
            if self.results['total_passwords'] > 0:
                f.write(f"- **Dictionary Matches**: {self.results['dictionary_matches']:,} ")
                f.write(f"({self.results['dictionary_matches']/self.results['total_passwords']*100:.2f}%)\n")
                f.write(f"- **L33t Speak Detected**: {self.results['leet_matches']:,} ")
                f.write(f"({self.results['leet_matches']/self.results['total_passwords']*100:.2f}%)\n")
                f.write(f"- **Keyboard Patterns**: {self.results['keyboard_patterns']:,} ")
                f.write(f"({self.results['keyboard_patterns']/self.results['total_passwords']*100:.2f}%)\n\n")
            else:
                f.write(f"- **Dictionary Matches**: No passwords analyzed\n")
                f.write(f"- **L33t Speak Detected**: No passwords analyzed\n")
                f.write(f"- **Keyboard Patterns**: No passwords analyzed\n\n")
            
            f.write("## Tools Used\n\n")
            f.write("- **Dictionary Lookup**: english-words library\n")
            f.write("- **POS Tagging**: spaCy (en_core_web_sm) + NLTK WordNet\n")
            f.write("- **Semantic Analysis**: WordNet definitions\n\n")
            
            f.write("## Part-of-Speech Classification\n\n")
            for pos, count in sorted(self.results['word_pos_tags'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"### {pos.upper().replace('_', ' ')}\n")
                f.write(f"Occurrences: {count}\n\n")
                top_words = self.results['top_words_by_pos'].get(pos, {})
                for word, word_count in list(top_words.items())[:10]:
                    definition = ""
                    if pos in self.results['wordnet_examples'] and word in self.results['wordnet_examples'][pos]:
                        definition = f"\n   *Definition: {self.results['wordnet_examples'][pos][word]}*\n"
                    f.write(f"- **{word}**: {word_count}{definition}\n")
                f.write("\n")
            
            f.write("## Pattern Type Ranking\n\n")
            pattern_types = sorted(
                self.results['pattern_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for rank, (pattern_type, count) in enumerate(pattern_types, 1):
                percentage = (count / sum(v for _, v in pattern_types) * 100)
                f.write(f"{rank}. **{pattern_type}**: {count:,} ({percentage:.2f}%)\n")
        
        print(f" Report saved to {report_file}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Step 4: Semantic Decomposition Analysis using Libraries"
    )
    parser.add_argument(
        "--data-file",
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'archive', '100k-most-used-passwords-NCSC.txt'),
        help="Path to the password dataset file",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Limit analysis to N passwords (for testing)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Output directory for results",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    data_file = args.data_file
    if not os.path.exists(data_file):
        print(f"Dataset file not found: {data_file}")
        return
    analyzer = SemanticDecompositionAnalyzer(data_file)
    analyzer.analyze(sample_size=args.sample)
    analyzer.save_results(args.output_dir)


if __name__ == "__main__":
    main()