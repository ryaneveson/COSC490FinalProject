import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from step6_grading import PasswordGrader, load_step5_counts, load_step4_results

# --- Semantic/NLP Libraries ---
"""
Additional libraries for advanced pattern-based attacks:
- zxcvbn-python: password pattern analysis and feedback
- pygtrie: efficient prefix tree for dictionary/pattern matching
- regex: advanced regular expressions
- Levenshtein: fuzzy matching for similar words/patterns
- markovify: Markov model-based password guess generation
"""
try:
    from zxcvbn import zxcvbn
except ImportError:
    zxcvbn = None
    print("zxcvbn-python not installed. Install with: pip install zxcvbn")
try:
    import pygtrie
except ImportError:
    pygtrie = None
    print("pygtrie not installed. Install with: pip install pygtrie")
try:
    import regex as re2
except ImportError:
    re2 = None
    print("regex not installed. Install with: pip install regex")
try:
    import Levenshtein
except ImportError:
    Levenshtein = None
    print("python-Levenshtein not installed. Install with: pip install python-Levenshtein")
try:
    import markovify
except ImportError:
    markovify = None
    print("markovify not installed. Install with: pip install markovify")
try:
    from english_words import get_english_words_set
    ENGLISH_WORDS = get_english_words_set(["web2"], lower=True)
except ImportError:
    ENGLISH_WORDS = set()
    print("english-words not installed. Install with: pip install english-words")
try:
    import spacy
    NLP = spacy.load('en_core_web_sm')
except Exception:
    NLP = None
    print("spaCy or model not installed. Install with: pip install spacy && python -m spacy download en_core_web_sm")
try:
    from nltk.corpus import wordnet
    from nltk import download as nltk_download
    try:
        wordnet.synsets('test')
    except:
        nltk_download('wordnet', quiet=True)
        nltk_download('averaged_perceptron_tagger', quiet=True)
        nltk_download('punkt', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("NLTK not installed. Install with: pip install nltk")
def extract_tokens(text):
    """Extract alphabetic tokens from text."""
    tokens = []
    current_token = []
    for char in text.lower():
        if char.isalpha():
            current_token.append(char)
        elif current_token:
            token = ''.join(current_token)
            if len(token) > 1:
                tokens.append(token)
            current_token = []
    if current_token:
        token = ''.join(current_token)
        if len(token) > 1:
            tokens.append(token)
    return tokens

def classify_word_pos(word):
    """Classify word by part of speech using spaCy > WordNet > unknown."""
    if NLP:
        doc = NLP(word.lower())
        if doc and len(doc) > 0:
            pos = doc[0].pos_
            if pos == 'PROPN':
                return 'proper_noun'
            elif pos == 'NOUN':
                return 'noun'
            elif pos == 'VERB':
                return 'verb'
            elif pos == 'ADJ':
                return 'adjective'
    if NLTK_AVAILABLE:
        synsets = wordnet.synsets(word.lower())
        if synsets:
            lexname = synsets[0].lexname()
            if 'person' in lexname:
                return 'proper_noun'
            elif 'noun' in lexname:
                return 'noun'
            elif 'verb' in lexname:
                return 'verb'
            elif 'adj' in lexname:
                return 'adjective'
    return 'unknown'

def get_high_priority_words(passwords, top_n=100):
    """Analyze passwords to extract most common names, nouns, etc."""
    word_counter = Counter()
    pos_counter = defaultdict(Counter)
    for pwd in passwords:
        tokens = extract_tokens(pwd)
        for token in tokens:
            if token in ENGLISH_WORDS:
                word_counter[token] += 1
                pos = classify_word_pos(token)
                pos_counter[pos][token] += 1
    # Get top words by POS
    top_names = [w for w, _ in pos_counter['proper_noun'].most_common(top_n)]
    top_nouns = [w for w, _ in pos_counter['noun'].most_common(top_n)]
    top_words = [w for w, _ in word_counter.most_common(top_n)]
    return {
        'names': top_names,
        'nouns': top_nouns,
        'words': top_words,
    }
from tqdm import tqdm

# Additional spear phishing support libraries
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    fake = None
    print("Faker not installed. Install with: pip install faker")
try:
    from nameparser import HumanName
except ImportError:
    HumanName = None
    print("nameparser not installed. Install with: pip install nameparser")
try:
    from dateutil.relativedelta import relativedelta
    from datetime import datetime
except ImportError:
    relativedelta = None
    print("python-dateutil not installed. Install with: pip install python-dateutil")
try:
    from email_validator import validate_email, EmailNotValidError
except ImportError:
    validate_email = None
    print("email-validator not installed. Install with: pip install email-validator")

def load_passwords(password_file):
    with open(password_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_pattern_types(step4_json):
    with open(step4_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Returns list of (pattern_type, count) sorted by count desc
    return sorted(data.get('pattern_types', {}).items(), key=lambda x: x[1], reverse=True)

# --- Leet speak substitution maps ---
LEET_MAP = {
    'a': ['4', '@'],
    'e': ['3'],
    'i': ['1', '!'],
    'o': ['0'],
    's': ['5', '$'],
    't': ['7'],
    'l': ['1'],
    'b': ['8'],
    'g': ['9'],
}

def leet_variants(word):
    """Generate multiple leet speak variants of a word."""
    variants = set()
    w = word.lower()
    # Single-substitution leet
    for i, ch in enumerate(w):
        if ch in LEET_MAP:
            for replacement in LEET_MAP[ch]:
                variants.add(w[:i] + replacement + w[i+1:])
    # Full leet (replace all)
    full = w
    for ch, replacements in LEET_MAP.items():
        full = full.replace(ch, replacements[0])
    variants.add(full)
    return variants

# --- Keyboard pattern dictionary ---
KEYBOARD_PATTERNS = [
    'qwerty', 'qwertyuiop', 'qwerty123', 'qwerty1', 'qwerty12',
    'asdfgh', 'asdfghjkl', 'asdf', 'asdf1234', 'asdfgh1',
    'zxcvbn', 'zxcvbnm', 'zxcvbnm1',
    '1qaz2wsx', '1q2w3e4r', '1q2w3e4r5t', '1q2w3e',
    'qazwsx', 'qaz123', 'qazwsxedc',
    '1234qwer', '123qwe', 'qwe123',
    'asdfjkl', 'zaq12wsx', 'zag12wsx',
    'mnbvcxz', 'poiuytrewq', 'lkjhgfdsa',
    'abcdef', 'abcdefg', 'abcdefgh', 'abcdefghij',
    'abc123', 'abc12345',
    'aaaaaa', 'bbbbbb', 'cccccc',
    'qweasd', 'qweasdzxc',
    'pass', 'passw0rd', 'p@ssword', 'p@ss', 'p@ssw0rd',
    'gwerty', 'gwerty123',
    '1g2w3e4r',
]

# --- Common digit sequences ---
def generate_digit_sequences():
    """Generate common digit-only password patterns."""
    digits = set()
    # Repeated digits: 000000, 111111, ..., 999999 at various lengths
    for d in '0123456789':
        for length in range(3, 11):
            digits.add(d * length)
    # Sequential: 123456, 1234567, 12345678, etc.
    seq = '1234567890'
    for start in range(10):
        for length in range(3, 11):
            s = ''.join(str((start + i) % 10) for i in range(length))
            digits.add(s)
    # Reverse sequential
    for length in range(3, 11):
        digits.add(''.join(str(i) for i in range(length, 0, -1)))
    digits.update(['654321', '987654321', '9876543210', '54321', '7654321'])
    # Repeated pairs: 121212, 123123, 112233, etc.
    for a in range(10):
        for b in range(10):
            pair = f"{a}{b}"
            digits.add(pair * 2)
            digits.add(pair * 3)
            digits.add(pair * 4)
    # Triple repeats: 123123, 456456
    for a in range(10):
        for b in range(10):
            for c in range(10):
                triple = f"{a}{b}{c}"
                digits.add(triple * 2)
    # Common dates: DDMMYYYY, MMDDYYYY patterns for years 1960-2025
    for year in range(1960, 2026):
        digits.add(str(year))
        digits.add(str(year)[-2:])  # 2-digit year
        for month in range(1, 13):
            for day in [1, 15, 28]:
                digits.add(f"{day:02d}{month:02d}{year}")
                digits.add(f"{month:02d}{day:02d}{year}")
                digits.add(f"{year}{month:02d}{day:02d}")
                digits.add(f"{day:02d}{month:02d}{year % 100:02d}")
    # Years with common prefixes
    return digits

# --- Common suffixes/prefixes for mutations ---
COMMON_SUFFIXES = [
    '', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
    '11', '12', '13', '14', '21', '22', '23', '69', '77', '99',
    '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
    '00', '07', '10', '15', '20', '21', '22', '23', '24', '25',
    '123', '234', '321', '007', '420', '666', '777', '000',
    '1234', '12345', '123456',
    '!', '!!', '@', '#', '$', '*', '!@', '!1', '@1', '#1',
    '!123', '@123',
    # Common years
    '1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999',
    '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009',
    '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019',
    '2020', '2021', '2022', '2023', '2024', '2025',
    '90', '91', '92', '93', '94', '95', '96', '97', '98', '99',
]

COMMON_PREFIXES = [
    '', '1', 'i', 'my', 'the',
]

def mutate_word(word):
    """Generate common mutations of a base word."""
    mutations = set()
    w_lower = word.lower()
    w_cap = word.capitalize()
    w_upper = word.upper()

    for base in [w_lower, w_cap, w_upper]:
        for suffix in COMMON_SUFFIXES:
            mutations.add(base + suffix)
        for prefix in COMMON_PREFIXES:
            mutations.add(prefix + base)

    # Leet speak variants
    for leet in leet_variants(w_lower):
        mutations.add(leet)
        for suffix in ['', '1', '123', '!', '12', '01']:
            mutations.add(leet + suffix)

    # Reversed
    mutations.add(w_lower[::-1])

    # word+word (doubling)
    mutations.add(w_lower + w_lower)

    return mutations

def extract_top_words_from_step4(step4_results, top_n=300):
    """Extract the most common words found in passwords from step4 analysis."""
    words = []
    matched = step4_results.get('matched_words', {})
    # Sort by frequency
    sorted_words = sorted(matched.items(), key=lambda x: x[1], reverse=True)
    for word, count in sorted_words[:top_n]:
        if len(word) >= 3:  # Skip very short tokens like 'ea', 'io'
            words.append(word)
    return words

def build_markov_guesses(passwords, num_guesses=50000):
    """Use Markov chain model to generate plausible password guesses."""
    guesses = set()
    if not markovify:
        return guesses
    # Build a text model treating each password as a "sentence" of characters
    # Use character-level Markov by joining chars with spaces
    char_corpus = '\n'.join(' '.join(pwd) for pwd in passwords[:20000] if 3 <= len(pwd) <= 16)
    try:
        model = markovify.NewlineText(char_corpus, state_size=2)
        for _ in range(num_guesses * 3):  # Oversample to account for None results
            sentence = model.make_short_sentence(max_chars=50, tries=5)
            if sentence:
                guess = sentence.replace(' ', '')
                if 3 <= len(guess) <= 20:
                    guesses.add(guess)
            if len(guesses) >= num_guesses:
                break
    except Exception as e:
        print(f"Markov generation warning: {e}")
    return guesses

def build_pattern_guess_set(step4_results, passwords):
    """Build a comprehensive set of password guesses using multiple attack strategies."""
    print("Building comprehensive guess set...")
    guesses = set()

    # --- Strategy 1: Top words from semantic analysis + mutations ---
    top_words = extract_top_words_from_step4(step4_results, top_n=300)
    print(f"  Strategy 1: Mutating {len(top_words)} top words from step4...")
    for word in tqdm(top_words, desc="  Word mutations"):
        guesses.update(mutate_word(word))

    # --- Strategy 2: Common names + mutations ---
    from step6_grading import COMMON_FIRST_NAMES
    print(f"  Strategy 2: Mutating {len(COMMON_FIRST_NAMES)} common names...")
    for name in tqdm(COMMON_FIRST_NAMES, desc="  Name mutations"):
        guesses.update(mutate_word(name))

    # --- Strategy 3: Digit-only sequences ---
    print("  Strategy 3: Generating digit sequences...")
    guesses.update(generate_digit_sequences())

    # --- Strategy 4: Keyboard patterns ---
    print("  Strategy 4: Adding keyboard patterns...")
    for kp in KEYBOARD_PATTERNS:
        guesses.add(kp)
        guesses.add(kp + '1')
        guesses.add(kp + '123')
        guesses.add(kp + '!')

    # --- Strategy 5: Compound words (word+word) ---
    print("  Strategy 5: Compound words (top 50 x top 50)...")
    short_words = [w for w in top_words[:50] if len(w) <= 8]
    for w1 in short_words:
        for w2 in short_words:
            guesses.add(w1 + w2)
            guesses.add(w1 + w2 + '1')
            guesses.add(w1 + w2 + '123')

    # --- Strategy 6: "iloveyou" style phrases ---
    print("  Strategy 6: Common phrase patterns...")
    phrase_starters = ['ilove', 'ilov', 'love', 'my', 'the', 'fuck', 'sexy']
    for starter in phrase_starters:
        for word in top_words[:100]:
            guesses.add(starter + word)
            guesses.add(starter + word + '1')
            guesses.add(starter + word + '123')
            guesses.add(starter + word + '!')

    # --- Strategy 7: Markov chain generated passwords ---
    print("  Strategy 7: Markov chain generation...")
    markov_guesses = build_markov_guesses(passwords, num_guesses=50000)
    guesses.update(markov_guesses)
    print(f"    Generated {len(markov_guesses)} Markov guesses")

    # --- Strategy 8: zxcvbn-based weakness exploitation ---
    if zxcvbn:
        print("  Strategy 8: zxcvbn feedback exploitation...")
        # Analyze a sample of passwords for common patterns zxcvbn identifies
        sample = random.sample(passwords, min(5000, len(passwords)))
        zxcvbn_words = set()
        for pwd in sample:
            try:
                result = zxcvbn(pwd)
                for match in result.get('sequence', []):
                    token = match.get('token', '')
                    if len(token) >= 3:
                        zxcvbn_words.add(token.lower())
            except Exception:
                pass
        print(f"    Found {len(zxcvbn_words)} unique tokens via zxcvbn")
        for word in zxcvbn_words:
            guesses.update(mutate_word(word))

    # --- Strategy 9: Fuzzy matching with Levenshtein ---
    if Levenshtein and len(top_words) > 0:
        print("  Strategy 9: Levenshtein fuzzy variants...")
        # Generate close variants of top words (edit distance 1)
        for word in top_words[:100]:
            w = word.lower()
            # Substitution at each position
            for i in range(len(w)):
                for c in 'abcdefghijklmnopqrstuvwxyz0123456789':
                    variant = w[:i] + c + w[i+1:]
                    guesses.add(variant)
            # Insertion at each position
            for i in range(len(w) + 1):
                for c in 'abcdefghijklmnopqrstuvwxyz0123456789':
                    variant = w[:i] + c + w[i:]
                    guesses.add(variant)
            # Deletion at each position
            for i in range(len(w)):
                variant = w[:i] + w[i+1:]
                if len(variant) >= 3:
                    guesses.add(variant)

    print(f"  Total unique guesses generated: {len(guesses):,}")
    return guesses

def attack_passwords_pattern(passwords, guess_set):
    """Attack passwords using a pre-built guess set with O(1) hash lookup."""
    cracked = {}
    total_guesses = len(guess_set)
    for pwd in tqdm(passwords, desc="Pattern Attack"):
        if pwd in guess_set:
            cracked[pwd] = {'attempts': total_guesses, 'pattern_type': 'pattern_match'}
        elif pwd.lower() in guess_set:
            cracked[pwd] = {'attempts': total_guesses, 'pattern_type': 'case_insensitive_match'}
    return cracked, total_guesses

def spear_phishing_guesses(context_words, step4_results, max_guesses=500000):
    """Generate spear phishing guesses: targeted personal info + mutation combos."""
    guesses = set()
    years = [str(y) for y in range(1970, 2026)]
    short_years = [str(y)[-2:] for y in range(1970, 2026)]

    # Use Faker to generate names, emails
    faker_names = []
    if fake:
        faker_names = [fake.first_name().lower() for _ in range(50)] + [fake.last_name().lower() for _ in range(50)]

    # Use nameparser to extract name parts
    parsed_names = []
    if HumanName:
        for word in context_words[:200]:
            try:
                name = HumanName(word)
                if name.first:
                    parsed_names.append(name.first.lower())
                if name.last:
                    parsed_names.append(name.last.lower())
            except Exception:
                pass

    # Date-based guesses
    date_suffixes = years + short_years
    if relativedelta:
        now = datetime.now()
        for i in range(40):
            date = now - relativedelta(years=i)
            date_suffixes.append(date.strftime('%m%d'))
            date_suffixes.append(date.strftime('%d%m'))

    # All name sources
    all_names = list(set(context_words + faker_names + parsed_names))

    # Common personal suffixes
    personal_suffixes = [
        '', '1', '2', '3', '11', '12', '13', '21', '22', '23', '69', '77', '99',
        '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
        '123', '1234', '12345', '321', '007', '420', '666', '777',
        '!', '!!', '@', '#', '$', '@1', '@123', '!1', '!123',
        '_1', '_123',
    ]

    print(f"  Spear phishing: mutating {len(all_names)} name sources...")
    for word in all_names:
        w_lower = word.lower()
        w_cap = word.capitalize()
        for base in [w_lower, w_cap]:
            for suffix in personal_suffixes:
                guesses.add(base + suffix)
            for year in years:
                guesses.add(base + year)
                guesses.add(year + base)
            for sy in short_years:
                guesses.add(base + sy)
        # Leet speak
        for leet in leet_variants(w_lower):
            guesses.add(leet)
            guesses.add(leet + '1')
            guesses.add(leet + '123')
        # Email-style
        guesses.add(f"{w_lower}@123")
        guesses.add(f"{w_lower}2020!")
        guesses.add(f"{w_lower}!")

    # Faker emails
    if fake:
        for _ in range(20):
            email = fake.email()
            guesses.add(email)

    # Name combinations
    short_names = [n for n in all_names if len(n) <= 8][:50]
    for n1 in short_names:
        for n2 in short_names:
            if n1 != n2:
                guesses.add(n1 + n2)
                guesses.add(n1 + n2 + '1')

    # Phrase patterns with names
    for name in all_names[:100]:
        guesses.add(f"ilove{name}")
        guesses.add(f"ilove{name}1")
        guesses.add(f"love{name}")
        guesses.add(f"my{name}")
        guesses.add(f"my{name}1")
        guesses.add(f"{name}ismine")
        guesses.add(f"{name}4ever")

    print(f"  Total spear phishing guesses: {len(guesses):,}")
    return guesses

def attack_passwords_spear(passwords, guess_set):
    """Attack passwords using spear phishing guess set."""
    cracked = {}
    total_guesses = len(guess_set)
    for pwd in tqdm(passwords, desc="Spear Phishing Attack"):
        if pwd in guess_set:
            cracked[pwd] = {'attempts': total_guesses, 'pattern_type': 'spear_phishing'}
        elif pwd.lower() in guess_set:
            cracked[pwd] = {'attempts': total_guesses, 'pattern_type': 'spear_case_insensitive'}
    return cracked, total_guesses

def write_report(filepath, title, passwords, cracked, total_guesses):
    """Write attack report with summary statistics."""
    cracked_count = len(cracked)
    total_count = len(passwords)
    pct = (cracked_count / total_count * 100) if total_count > 0 else 0

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'# {title}\n\n')
        f.write(f'## Summary\n\n')
        f.write(f'- **Total passwords tested**: {total_count:,}\n')
        f.write(f'- **Total unique guesses generated**: {total_guesses:,}\n')
        f.write(f'- **Passwords cracked**: {cracked_count:,} ({pct:.1f}%)\n')
        f.write(f'- **Passwords not cracked**: {total_count - cracked_count:,} ({100-pct:.1f}%)\n\n')

        # Breakdown by attack type
        type_counts = Counter(info['pattern_type'] for info in cracked.values())
        if type_counts:
            f.write(f'## Crack Breakdown by Method\n\n')
            f.write('| Method | Count | % of Cracked |\n')
            f.write('|--------|-------|--------------|\n')
            for method, count in type_counts.most_common():
                f.write(f'| {method} | {count:,} | {count/cracked_count*100:.1f}% |\n')
            f.write('\n')

        # Sample of cracked passwords
        f.write(f'## Sample Cracked Passwords (first 200)\n\n')
        f.write('| Password | Attack Type |\n')
        f.write('|----------|-------------|\n')
        shown = 0
        for pwd in passwords:
            if pwd in cracked and shown < 200:
                info = cracked[pwd]
                f.write(f"| {pwd} | {info['pattern_type']} |\n")
                shown += 1

        # Sample of NOT cracked passwords
        f.write(f'\n## Sample Uncracked Passwords (first 100)\n\n')
        f.write('| Password |\n')
        f.write('|----------|\n')
        shown = 0
        for pwd in passwords:
            if pwd not in cracked and shown < 100:
                f.write(f"| {pwd} |\n")
                shown += 1

def main():
    parser = argparse.ArgumentParser(description="Step 8: Attack Simulation")
    parser.add_argument('--password_file', 
        default=str(Path(__file__).parent.parent / 'data' / 'archive' / '100k-most-used-passwords-NCSC.txt'),
        help='File with passwords to attack. By default, uses the 100k-most-used-passwords-NCSC.txt dataset. You can specify another file if desired.'
    )
    parser.add_argument('--step5_json', default=str(Path(__file__).parent / "step5_probabilistic_summary.json"))
    parser.add_argument('--step4_json', default=str(Path(__file__).parent / "step4_semantic_results.json"))
    parser.add_argument('--context_words', nargs='*', default=['password', 'admin', 'user', 'test', 'welcome'])
    parser.add_argument('--output', default=str(Path(__file__).parent / 'STEP8_ATTACK_REPORT.md'))
    args = parser.parse_args()

    passwords = load_passwords(args.password_file)
    pattern_types = load_pattern_types(args.step4_json)
    step5_counts = load_step5_counts(Path(args.step5_json))
    step4_results = load_step4_results(Path(args.step4_json))
    grader = PasswordGrader(step5_counts, step4_results)

    # --- Semantic Analysis for Attack Context ---
    print("Analyzing dataset for high-priority attack words (names, nouns, common words)...")
    high_priority = get_high_priority_words(passwords, top_n=200)
    attack_context_words = list(set(
        high_priority['names'] + high_priority['nouns'] + high_priority['words']
    ))
    print(f"Found {len(attack_context_words)} unique attack context words")
    print(f"Top attack context words: {attack_context_words[:20]} ...")

    # ============================================================
    # PATTERN-BASED ATTACK
    # ============================================================
    print("\n" + "="*60)
    print("PATTERN-BASED ATTACK")
    print("="*60)
    pattern_guess_set = build_pattern_guess_set(step4_results, passwords)
    # Also add lowercase versions for case-insensitive matching
    lowercase_set = {g.lower() for g in pattern_guess_set}
    pattern_guess_set.update(lowercase_set)
    print(f"Final pattern guess set size: {len(pattern_guess_set):,}")

    cracked_pattern, pattern_total = attack_passwords_pattern(passwords, pattern_guess_set)
    pattern_cracked_count = len(cracked_pattern)
    print(f"\nPattern attack: {pattern_cracked_count:,} cracked / {len(passwords):,} tested "
          f"({pattern_cracked_count/len(passwords)*100:.1f}%)")

    pattern_report = str(Path(args.output).parent / 'STEP8_PATTERN_ATTACK_REPORT.md')
    write_report(pattern_report,
                 'Step 8: Pattern-Based Attack Simulation Report',
                 passwords, cracked_pattern, pattern_total)
    print(f"Pattern report saved to {pattern_report}")

    # ============================================================
    # SPEAR PHISHING ATTACK
    # ============================================================
    print("\n" + "="*60)
    print("SPEAR PHISHING ATTACK")
    print("="*60)
    spear_guess_set = spear_phishing_guesses(attack_context_words, step4_results)
    # Also add lowercase versions
    spear_lowercase = {g.lower() for g in spear_guess_set}
    spear_guess_set.update(spear_lowercase)
    print(f"Final spear phishing guess set size: {len(spear_guess_set):,}")

    cracked_spear, spear_total = attack_passwords_spear(passwords, spear_guess_set)
    spear_cracked_count = len(cracked_spear)
    print(f"\nSpear phishing: {spear_cracked_count:,} cracked / {len(passwords):,} tested "
          f"({spear_cracked_count/len(passwords)*100:.1f}%)")

    spear_report = str(Path(args.output).parent / 'STEP8_SPEAR_ATTACK_REPORT.md')
    write_report(spear_report,
                 'Step 8: Spear Phishing Attack Simulation Report',
                 passwords, cracked_spear, spear_total)
    print(f"Spear phishing report saved to {spear_report}")

    # ============================================================
    # COMBINED SUMMARY
    # ============================================================
    all_cracked = set(cracked_pattern.keys()) | set(cracked_spear.keys())
    print(f"\n{'='*60}")
    print(f"COMBINED RESULTS")
    print(f"{'='*60}")
    print(f"Pattern attack:   {pattern_cracked_count:,} cracked ({pattern_cracked_count/len(passwords)*100:.1f}%)")
    print(f"Spear phishing:   {spear_cracked_count:,} cracked ({spear_cracked_count/len(passwords)*100:.1f}%)")
    print(f"Combined unique:  {len(all_cracked):,} cracked ({len(all_cracked)/len(passwords)*100:.1f}%)")

    # ============================================================
    # SAVE JSON RESULTS FOR STEP 9
    # ============================================================
    json_output = {
        "total_passwords": len(passwords),
        "pattern_attack": {
            "total_guesses": pattern_total,
            "cracked_count": pattern_cracked_count,
            "success_rate": round(pattern_cracked_count / len(passwords) * 100, 2),
            "cracked_passwords": {
                pwd: info for pwd, info in cracked_pattern.items()
            },
        },
        "spear_attack": {
            "total_guesses": spear_total,
            "cracked_count": spear_cracked_count,
            "success_rate": round(spear_cracked_count / len(passwords) * 100, 2),
            "cracked_passwords": {
                pwd: info for pwd, info in cracked_spear.items()
            },
        },
        "combined_cracked_count": len(all_cracked),
        "combined_success_rate": round(len(all_cracked) / len(passwords) * 100, 2),
        "all_passwords": passwords,
    }

    json_path = str(Path(args.output).parent / 'step8_attack_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    print(f"JSON results saved to {json_path}")

if __name__ == "__main__":
    main()
