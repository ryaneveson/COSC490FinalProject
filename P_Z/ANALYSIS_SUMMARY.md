# Phase 1: Structural Analysis - Steps 2 & 3 Summary

## Overview
Analysis of 71,149,350 passwords from files P-Z and Symbols directory of the RockYou password dataset.

---

## Step 2: General Analysis

### Basic Statistics
- **Total Passwords**: 71,149,350
- **Unique Passwords**: 71,149,350  
- **Duplicate Rate**: 0% (all passwords are unique at the top level)

### Password Length Distribution
| Length | Count | Percentage |
|--------|-------|-----------|
| 8 | 3,679,932 | 5.17% |
| 9 | 20,161,172 | **28.34%** ⭐ |
| 10 | 3,060,792 | 4.30% |
| 11 | 3,601,638 | 5.06% |
| 12 | 15,608,273 | **21.94%** ⭐ |
| 13 | 3,154,255 | 4.43% |
| 14-32 | Remaining | 11.76% |

**Key Insight**: Most passwords are 9 or 12 characters long, accounting for 50% of the dataset.

### Length Statistics
```
  Min:     8 characters
  Max:     32 characters
  Mean:    13.28 characters
  Median:  12.00 characters
```

### Character Type Variability
| Character Type | Count | Percentage |
|---|---|---|
| Contains Digits | 71,149,350 | **100%** |
| Contains Uppercase | 71,149,350 | **100%** |
| Contains Lowercase | 71,149,350 | **100%** |
| Contains Special Chars | 71,149,350 | **100%** |

**Key Insight**: ALL passwords in the dataset contain all 4 character types - this is a highly structured and complex dataset.

### Statistics by File Category
| Category | Total | Unique | Avg Length | Notes |
|----------|-------|--------|------------|-------|
| P | 6,438,232 | 6,438,232 | 13.70 | Starting with P |
| Q | 2,330,379 | 2,330,379 | 16.21 | Longest avg length |
| R | 6,133,677 | 6,133,677 | 13.49 | |
| S | 6,653,179 | 6,653,179 | 13.85 | |
| T | 4,590,076 | 4,590,076 | 13.93 | |
| U | 3,979,858 | 3,979,858 | 14.21 | |
| V | 4,297,234 | 4,297,234 | 14.06 | |
| W | 4,227,081 | 4,227,081 | 14.57 | |
| X | 2,793,280 | 2,793,280 | 15.30 | Smaller subset |
| Y | 3,290,066 | 3,290,066 | 14.59 | |
| Z | 2,879,550 | 2,879,550 | 15.34 | Smaller subset |
| **Symbols** | **23,536,738** | **23,536,738** | **11.33** | **Largest category, shortest avg** |

**Key Insight**: The Symbols category represents 33% of all passwords and has the shortest average length (11.33 chars).

---

## Step 3: Password Pattern Analysis

### Mask Definition
- **C** = Uppercase Letter
- **L** = Lowercase Letter  
- **D** = Digit
- **S** = Special Character

### Pattern Statistics
- **Total Passwords Analyzed**: 71,149,350
- **Unique Masks**: 12,120,141 (17% of total passwords have unique masks)
- **Average Mask Occurrence**: 5.87 passwords per mask

### Complexity Analysis
```
All 4 character sets (CLDS): 71,149,350 (100%)
```

**Key Insight**: Every single password contains all four character types - indicating very high complexity and structured generation.

### Top 30 Most Frequent Password Masks

| Rank | Mask | Count | Percentage |
|------|------|-------|-----------|
| 1 | C L L L L S D D D D | 350,580 | 0.49% |
| 2 | C L L L L L S D D | 243,597 | 0.34% |
| 3 | C L L L L S D D | 240,498 | 0.34% |
| 4 | C L L L L L S D D D D | 239,947 | 0.34% |
| 5 | S D D C L L L L L | 238,534 | 0.34% |
| 6-10 | Various | ~235,000 each | 0.33% |
| 11 | S D D C C C C L L | 235,351 | 0.33% |
| 12 | C L L L L L L S D D D D | 194,334 | 0.27% |
| 13-30 | Various patterns | Decreasing | < 0.27% |

**Key Observations**:
1. Even the most common mask only accounts for 0.49% of passwords
2. The top mask follows pattern: **1 Capital + 4-5 Lowercase + 1 Special + 3-4 Digits**
3. Top 30 masks account for only ~5% of the dataset
4. High diversity in mask patterns suggests varied password generation

### Pattern Structure Analysis
Most frequent pattern structures include:
- **Capital + Multiple lowercase + Special + Multiple digits**
  - Example: C LLLL S DDDD
  - Pattern: `Word + Symbol + Number`
  
- **Special + Digits + Mixed case letters**
  - Example: S DD CCC LL
  - Pattern: `Symbol + Number + Mixed Word`

- **Capital + Long lowercase + 1 Special + Multiple digits**
  - Example: C LLL S DDDD
  - Pattern: `Word + Symbol + Number`

### Mask Length Distribution
Masks follow the same distribution as password lengths:

| Length | Unique Masks | Percentage |
|--------|---|---|
| 8 | 30,618 | 0.25% |
| 9 | 106,755 | 0.88% |
| 10 | 216,905 | 1.79% |
| 11 | 329,191 | 2.72% |
| 12 | 771,973 | **6.37%** ⭐ |
| 13 | 638,286 | 5.27% |
| 14+ | Remaining | ~30% |

**Key Insight**: 12-character passwords have the most unique mask variations (771,973), suggesting this length offers the most flexibility in character arrangement.

### Character Set Pattern
All passwords follow exactly one pattern:
```
100% = Capital + Lowercase + Digit + Special (CLDS)
```

This means:
- Every password MUST have at least one of each: uppercase, lowercase, digit, special character
- This suggests these passwords were generated with strict requirements
- Very high complexity/entropy by design

---

## Overall Findings & Implications

### Dataset Characteristics
1. **Highly Structured**: Not natural passwords - all contain all 4 character types
2. **Non-Randomly Distributed**: Most passwords 9-12 characters, peaking at these lengths
3. **Extremely Diverse**: 12.1 million unique masks out of 71 million passwords
4. **Well-Distributed**: No single mask dominates (highest is only 0.49%)

### Most Common Password Patterns (Semantic)
Based on top masks, the most frequent pattern appears to be:
- **Pattern**: `CapitalizedWord + Special + Numbers`
- **Example Masks**: `Pinch$5678`, `Mouse@1234`, `Heart#2021`
- **Frequency**: ~0.5-0.3% of passwords follow similar structures

### Password Generation Insights
- The Symbols category (33% of data) drives lowercase/short-password averages
- Q category has longest average (16.21 chars) - may contain different password types
- Natural passwords would show single-type dominance; these are all enforced-complexity

### Recommendations for Phase 2-4
1. **For L33t Detection**: Look for digit-letter substitution patterns (3→E, 4→A, etc.)
2. **For Semantic Analysis**: Pre-process words from CLLLL or LLLL portions
3. **For Keyboard Patterns**: Check special character positions relative to digits
4. **For Grading**: Weight penalties for short passwords (8-10) and highly common masks
5. **For Attack Simulation**: Prioritize testing most common masks first

---

## Output Files Generated
- `step2_results.json` - Complete Step 2 analysis data
- `step3_results.json` - Complete Step 3 analysis data  
- `step3_top_masks.txt` - Human-readable top mask list
- `ANALYSIS_SUMMARY.md` - This file

---

**Analysis Completed**: Both Step 2 and Step 3 successfully analyzed 71.1+ million passwords from P-Z and Symbols categories.
