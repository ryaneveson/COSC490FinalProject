# Step 4: Semantic Decomposition Report

## Executive Summary

- **Total Passwords Analyzed**: 99,839
- **Dictionary Used**: english-words library (234,450 words)
- **Dictionary Matches**: 37,358 (37.42%)
- **L33t Speak Detected**: 3,297 (3.30%)
- **Keyboard Patterns**: 9,228 (9.24%)

## Tools Used

- **Dictionary Lookup**: english-words library
- **POS Tagging**: spaCy (en_core_web_sm) + NLTK WordNet
- **Semantic Analysis**: WordNet definitions

## Part-of-Speech Classification

### PROPER NOUN
Occurrences: 16443

- **ea**: 668
   *Definition: the Babylonian god of wisdom; son of Apsu and father of Marduk; counterpart of the Sumerian Enki; as one of the supreme triad including Anu and Bel he was assigned control of the watery element*

- **password**: 190
   *Definition: a secret word or phrase known only to a restricted group*

- **alex**: 120
- **ie**: 107
- **iao**: 107
- **monkey**: 105
- **chris**: 100
- **ge**: 97
- **daniel**: 85
- **jesus**: 85

### NOUN
Occurrences: 13277

- **love**: 256
   *Definition: a strong positive emotion of regard and affection*

- **io**: 236
   *Definition: (Greek mythology) a maiden seduced by Zeus; when Hera was about to discover them together Zeus turned her into a white heifer*

- **angel**: 135
   *Definition: spiritual being attendant upon God*

- **football**: 121
- **be**: 107
- **dragon**: 97
- **baby**: 92
- **princess**: 90
- **money**: 89
- **life**: 88

### VERB
Occurrences: 4096

- **go**: 170
   *Definition: a time for working (after which you will be relieved by someone else)*

- **gi**: 153
   *Definition: a unit of magnetomotive force equal to 0.7958 ampere-turns*

- **ai**: 105
   *Definition: an agency of the United States Army responsible for providing timely and relevant and accurate and synchronized intelligence to tactical and operational and strategic level commanders*

- **ba**: 105
- **ga**: 93
- **ao**: 84
- **bitch**: 78
- **sunshine**: 63
- **is**: 50
- **pimp**: 49

### ADJECTIVE
Occurrences: 2665

- **sexy**: 96
   *Definition: marked by or tending to arouse sexual desire or interest*

- **blue**: 85
   *Definition: blue color or pigment; resembling the color of the clear sky in the daytime*

- **happy**: 65
   *Definition: enjoying or showing or marked by joy or pleasure*

- **pink**: 60
- **lucky**: 57
- **black**: 55
- **yellow**: 51
- **sweet**: 45
- **lovely**: 44
- **cool**: 44

### ADVERB
Occurrences: 945

- **so**: 107
   *Definition: the syllable naming the fifth (dominant) note of any musical scale in solmization*

- **ever**: 47
   *Definition: at any time*

- **forever**: 40
   *Definition: for a limitless time; ; - P.P.Bliss*

- **emily**: 40
- **oliver**: 37
- **os**: 36
- **molly**: 35
- **aaron**: 33
- **slipknot**: 32
- **pretty**: 32

### ADPOSITION
Occurrences: 432

- **bo**: 180
- **as**: 98
   *Definition: a very poisonous metallic element that has three allotropic forms; arsenic and arsenic compounds are used as herbicides and insecticides and various alloys; found in arsenopyrite and orpiment and realgar*

- **og**: 41
- **ta**: 32
- **te**: 22
- **at**: 15
- **in**: 5
- **under**: 4
- **bluebird**: 3
- **amy**: 3

### PRONOUN
Occurrences: 338

- **me**: 77
   *Definition: a state in New England*

- **my**: 39
- **you**: 34
- **whatever**: 31
- **it**: 28
- **all**: 15
- **nothing**: 13
- **the**: 13
- **we**: 9
- **an**: 8

### INTERJECTION
Occurrences: 305

- **hello**: 71
   *Definition: an expression of greeting*

- **ti**: 65
   *Definition: a light strong grey lustrous corrosion-resistant metallic element used in strong lightweight alloys (as for airplane parts); the main sources are rutile and ilmenite*

- **oe**: 40
- **hi**: 14
- **er**: 12
- **no**: 10
- **la**: 9
- **please**: 9
- **ok**: 8
- **da**: 7

### UNKNOWN
Occurrences: 141

- **to**: 89
- **sai**: 15
- **nicolas**: 10
- **di**: 8
- **shalom**: 4
- **kari**: 3
- **electro**: 2
- **bon**: 2
- **ye**: 2
- **elohim**: 1

### NUMBER
Occurrences: 138

- **one**: 17
   *Definition: the smallest whole number or a numeral representing this number*

- **zero**: 13
   *Definition: a quantity of no importance*

- **seven**: 10
   *Definition: the cardinal number that is the sum of six and one*

- **three**: 10
- **twenty**: 9
- **million**: 8
- **four**: 6
- **eleven**: 5
- **eight**: 5
- **fifty**: 4

### SUBORDINATING CONJUNCTION
Occurrences: 15

- **if**: 9
- **because**: 2
- **why**: 2
   *Definition: the cause or intention underlying an action or situation, especially in the phrase `the whys and wherefores'*

- **how**: 1
- **that**: 1

### CONJUNCTION
Occurrences: 9

- **and**: 5
- **plus**: 1
   *Definition: a useful or valuable quality*

- **but**: 1
   *Definition: and nothing more*

- **nor**: 1
- **or**: 1

## Pattern Type Ranking

1. **word_digit**: 41,925 (41.99%)
2. **word_only**: 33,429 (33.48%)
3. **leet_speak**: 20,292 (20.32%)
4. **keyboard_pattern**: 2,347 (2.35%)
5. **word_special**: 1,289 (1.29%)
6. **word_special_digit_lower**: 340 (0.34%)
7. **other**: 105 (0.11%)
8. **digit_only**: 71 (0.07%)
9. **word_special_digit_mixed**: 37 (0.04%)
10. **word_special_digit_upper**: 4 (0.00%)
