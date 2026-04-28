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
| digit_only | -2 | Digits only |
| special_digit | -0 | Special characters + digits |
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
| `Password123!` | 35.67 | 40.67 | -20 | -25 | +40 | Base: 40.7 + Complexity: 40 - Pattern: 20 - Specific: 25 - Short: 0 - Name: 0 = 35.7 |
| `asdf` | 13.06 | 39.06 | -6 | -10 | +0 | Base: 39.1 + Complexity: 0 - Pattern: 6 - Specific: 10 - Short: 10 - Name: 0 = 13.1 |
| `Admin123!` | 37.2 | 40.2 | -8 | -25 | +30 | Base: 40.2 + Complexity: 30 - Pattern: 8 - Specific: 25 - Short: 0 - Name: 0 = 37.2 |
| `MySecurePass2024!` | 75.39 | 38.39 | -8 | -5 | +50 | Base: 38.4 + Complexity: 50 - Pattern: 8 - Specific: 5 - Short: 0 - Name: 0 = 75.4 |

## Top Specific Penalty Reasons

| Pattern | Penalty | Occurrences |
|---------|---------|-------------|
| `123$` | -7 | 3561 |
| `123456` | -10 | 733 |
| `1234$` | -9 | 611 |
| `!$` | -5 | 582 |
| `^pass` | -10 | 264 |
| `qwerty` | -10 | 219 |
| `password` | -15 | 179 |
| `asdf` | -10 | 154 |
| `admin` | -12 | 32 |
| `^admin` | -8 | 19 |

## Top 10 Password Grades from Real Data

| Rank | Password | Final Score | Base Pred | Pattern Pen | Specific Pen | Complexity Bonus |
|------|----------|-------------|-----------|-------------|--------------|------------------|
| 1 | `friendofYOUCANMAKE$200-` | 81.47 | 39.47 | -8 | -0 | +50 |
| 2 | `friendofEarning$1` | 81.34 | 39.34 | -8 | -0 | +50 |
| 3 | `$HEX[687474703a2f2f777777]` | 81.25 | 39.25 | -8 | -0 | +50 |
| 4 | `$HEX[687474703a2f2f616473]` | 80.55 | 38.55 | -8 | -0 | +50 |
| 5 | `Doomsayer.2.7mords.V` | 80.23 | 38.23 | -8 | -0 | +50 |
| 6 | `Doomsayer.2.7mords.VV` | 80.16 | 38.16 | -8 | -0 | +50 |
| 7 | `volodina.elena66` | 79.97 | 39.97 | -0 | -0 | +40 |
| 8 | `пїЅпїЅпїЅпїЅпїЅпїЅ@mail.ru` | 76.03 | 44.03 | -8 | -0 | +40 |
| 9 | `РјР°СЂРёРЅР°` | 74.32 | 44.32 | -0 | -0 | +30 |
| 10 | `РїР°СЂРѕР»СЊ` | 73.75 | 43.75 | -0 | -0 | +30 |

## Bottom 10 Password Grades from Real Data

| Rank | Password | Final Score | Base Pred | Pattern Pen | Specific Pen | Complexity Bonus |
|------|----------|-------------|-----------|-------------|--------------|------------------|
| 98567 | `ALEX` | 5.55 | 40.55 | -10 | -0 | +0 |
| 98568 | `JAMES` | 5.41 | 40.41 | -10 | -0 | +0 |
| 98569 | `mike123` | 5.18 | 42.18 | -15 | -7 | +5 |
| 98570 | `anna123` | 5.14 | 42.14 | -15 | -7 | +5 |
| 98571 | `alex123` | 4.81 | 41.81 | -15 | -7 | +5 |
| 98572 | `john1` | 4.8 | 39.8 | -15 | -0 | +5 |
| 98573 | `john` | 4.62 | 39.62 | -10 | -0 | +0 |
| 98574 | `john123` | 4.15 | 41.15 | -15 | -7 | +5 |
| 98575 | `DAVID` | 4.08 | 39.08 | -10 | -0 | +0 |
| 98576 | `john3` | 3.56 | 38.56 | -15 | -0 | +5 |

## Example Passwords by Grade

**Excellent (90-100):**

**Good (75-89):**
- `friendofYOUCANMAKE$200-`
- `friendofEarning$1`
- `$HEX[687474703a2f2f777777]`

**Fair (60-74):**
- `РјР°СЂРёРЅР°`
- `РїР°СЂРѕР»СЊ`
- `РјР°РєСЃРёРј`

**Weak (40-59):**
- `AVM6Ubdunj`
- `FupYuxTb66`
- `vika-selfish`

**Very Weak (0-39):**
- `12101988`
- `1dontknow`
- `12121983`

