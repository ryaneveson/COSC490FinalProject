# Step 6: Password Grading Report

## Methodology

Password strength grading combines multiple factors:

1. **Base Predictability Score** (0-100): From Step 5 probabilistic model
   - Higher score = more predictable (worse)
   - Based on n-gram character transition probabilities

2. **Pattern Type Penalties**: Based on Step 4 semantic analysis
   - More common pattern types get higher deductions
   - Examples: dictionary words, keyboard patterns, leet speak

3. **Specific Pattern Penalties**: Common weak patterns
   - Keyboard sequences (asdf, qwerty)
   - Common words (password, admin)
   - Simple suffixes (!, 123)

4. **Complexity Bonuses**: Length and character variety
   - Length: 8+ chars = +5, 12+ = +15, 16+ = +25
   - Character sets: 4 types (upper/lower/digit/special) = +25

## Scoring Components

| Component                | Range  | Description                                         |
|--------------------------|--------|-----------------------------------------------------|
| Base predictability      | 0–50   | Inverse of n-gram predictability (less predictable = higher, up to +50 pts) |
| Complexity bonus         | 0–50   | Length (+ up to 25 pts) + char-class diversity (+ up to 25 pts) |
| Pattern type penalty     | 0–20   | Deduction for common pattern types from Step 4 (up to -20 pts) |
| Specific pattern penalty | 0–25   | Keyboard runs, weak words, repeated chars, etc. (up to -25 pts) |

## Formula

```
final_score = base_predictability (max 50) + complexity_bonus (max 50)
              - pattern_type_penalty (max 20) - specific_pattern_penalty (max 25)
final_score = clamp(final_score, 0, 100)
```

## Points Allocation

- **Base predictability**: +0 to +50 points (less predictable = higher score)
- **Complexity bonus**: +0 to +50 points (length and character set diversity)
- **Pattern type penalty**: -0 to -20 points (common patterns)
- **Specific pattern penalty**: -0 to -25 points (weak substrings, keyboard walks, etc.)

## Pattern Type Penalties

| Pattern Type | Penalty | Description |
|-------------|---------|-------------|
| word_special_digit_mixed | -25 | Dictionary word + special + digit + mixed case |
| word_special_digit_upper | -20 | Dictionary word + special + digit + uppercase |
| word_special_digit_lower | -18 | Dictionary word + special + digit + lowercase |
| word_digit | -15 | Dictionary word + digits |
| word_special | -12 | Dictionary word + special characters |
| word_only | -10 | Dictionary word only |
| leet_speak | -8 | Leet speak substitutions |
| keyboard_pattern | -6 | Keyboard sequences |
| special_digit | -4 | Special characters + digits |
| digit_only | -2 | Digits only |
| other | -0 | Other patterns |

## Specific Pattern Penalties

- `asdf`: -10 points
- `qwerty`: -10 points
- `123456`: -10 points
- `password`: -15 points
- `admin`: -12 points
- `login`: -8 points
- `user`: -6 points
- `!$`: -5 points
- `!!$`: -8 points
- `123$`: -7 points
- `1234$`: -9 points
- `^admin`: -8 points
- `^user`: -6 points
- `^pass`: -10 points

## Complexity Bonuses

### Length Bonuses
- 8+ characters: +5 points
- 10+ characters: +10 points
- 12+ characters: +15 points
- 14+ characters: +20 points
- 16+ characters: +25 points

### Character Set Bonuses
- 1 types (uppercase): +0 points
- 2 types (uppercase, lowercase): +5 points
- 3 types (uppercase, lowercase, digits): +15 points
- 4 types (uppercase, lowercase, digits, special): +25 points

## Grading Scale

| Grade Range | Description         |
|-------------|--------------------|
| 90-100      | Excellent (Very Strong) |
| 75-89       | Good (Strong)      |
| 60-74       | Fair (Moderate)    |
| 40-59       | Weak               |
| 0-39        | Very Weak          |

## Test Password Grades

| Password | Final Score | Base Pred | Pattern Pen | Specific Pen | Complexity Bonus | Breakdown |
|----------|-------------|-----------|-------------|--------------|------------------|-----------|
| `Password123!` | 44.99 | 37.99 | -8 | -25 | +40 | Base: 38.0 + Complexity: 40 - Pattern: 8 - Specific: 25 = 45.0 |
| `asdf` | 24.15 | 40.15 | -6 | -10 | +0 | Base: 40.2 + Complexity: 0 - Pattern: 6 - Specific: 10 = 24.2 |
| `Admin123!` | 34.91 | 37.91 | -8 | -25 | +30 | Base: 37.9 + Complexity: 30 - Pattern: 8 - Specific: 25 = 34.9 |
| `MySecurePass2024!` | 73.37 | 36.37 | -8 | -5 | +50 | Base: 36.4 + Complexity: 50 - Pattern: 8 - Specific: 5 = 73.4 |

## Top Specific Penalty Reasons

| Pattern | Penalty | Occurrences |
|---------|---------|-------------|
| `!$` | -5 | 909471 |
| `123$` | -7 | 253701 |
| `asdf` | -10 | 236101 |
| `!!$` | -8 | 92435 |
| `1234$` | -9 | 86707 |
| `qwerty` | -10 | 77794 |
| `123456` | -10 | 36168 |
| `^pass` | -10 | 36130 |
| `password` | -15 | 22150 |
| `user` | -6 | 10660 |

## Top 10 Password Grades from Real Data

| Rank | Password | Final Score | Base Pred | Pattern Pen | Specific Pen | Complexity Bonus |
|------|----------|-------------|-----------|-------------|--------------|------------------|
| 1 | `xipifioxG6CatHBw==` | 87.05 | 41.05 | -4 | -0 | +50 |
| 2 | `u6gxG6CXvcvioxG6CatHBw==` | 86.75 | 40.75 | -4 | -0 | +50 |
| 3 | `YAYujkifgdfioxG6CatHBw==` | 86.53 | 40.53 | -4 | -0 | +50 |
| 4 | `PLfdoiovfgjioxG6CatHBw==` | 86.48 | 40.48 | -4 | -0 | +50 |
| 5 | `zvbvcUHBgenioxG6CatHBw==` | 86.47 | 40.47 | -4 | -0 | +50 |
| 6 | `VinderdthmnioxG6CatHBw==` | 86.45 | 40.45 | -4 | -0 | +50 |
| 7 | `WSlashToxGDioxG6CatHBw==` | 86.45 | 40.45 | -4 | -0 | +50 |
| 8 | `zjkhanvEuyrioxG6CatHBw==` | 86.43 | 40.43 | -4 | -0 | +50 |
| 9 | `yvnetratypPioxG6CatHBw==` | 86.42 | 40.42 | -4 | -0 | +50 |
| 10 | `VXCXvbcalfPioxG6CatHBw==` | 86.41 | 40.41 | -4 | -0 | +50 |

## Bottom 10 Password Grades from Real Data

| Rank | Password | Final Score | Base Pred | Pattern Pen | Specific Pen | Complexity Bonus |
|------|----------|-------------|-----------|-------------|--------------|------------------|
| 71149341 | `#1SaRa!!` | 32.8 | 35.8 | -20 | -13 | +30 |
| 71149342 | `sw4evA!!` | 32.56 | 35.56 | -20 | -13 | +30 |
| 71149343 | `#1sArA!!` | 32.51 | 35.51 | -20 | -13 | +30 |
| 71149344 | `SW4EVa!!` | 32.3 | 35.3 | -20 | -13 | +30 |
| 71149345 | `T1c4eva!!` | 32.3 | 35.3 | -20 | -13 | +30 |
| 71149346 | `Pass5wer!` | 32.18 | 37.18 | -20 | -15 | +30 |
| 71149347 | `VS4eva!!` | 32.0 | 35.0 | -20 | -13 | +30 |
| 71149348 | `PG4eva!!` | 31.92 | 34.92 | -20 | -13 | +30 |
| 71149349 | `password0.POI` | 31.41 | 36.41 | -20 | -25 | +40 |
| 71149350 | `Pass4eva!` | 30.89 | 35.89 | -20 | -15 | +30 |

## Example Passwords by Grade

**Excellent (90-100):**

**Good (75-89):**
- `xipifioxG6CatHBw==`
- `u6gxG6CXvcvioxG6CatHBw==`
- `YAYujkifgdfioxG6CatHBw==`

**Fair (60-74):**
- `p######)~O(-_0)`
- `P######)~o(0_<)`
- `P######@*_*>-b0`

**Weak (40-59):**
- `P!145ter`
- `P!@#456p`
- `P!GGYb@CK5`

**Very Weak (0-39):**
- `PaSSw0rd!!`
- `Paul-1234`
- `R3xAdMIN!`

