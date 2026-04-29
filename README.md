# Password-Analysis project


#### Group members:
| Group 1 | | Group 2 | |
| :--- | :--- | :--- | :--- |
| **Student Name** | **Student Number** | **Student Name** | **Student Number** |
| Ryan Eveson | 99775389 | Devin Huang | 86828886 |
| Joaquin Almora | 68642073 | Maria Sato | 14489231 |
| Phong Nguyen | 55533582 | Leila Saparbek | 
|| | Ali Afoud | 34031898 | 


---
### Phase 1: Structural Analysis
Objective is analysing the data of password, their patterns and more...

- **Step 1: dataset acquisition** Retrieving a password dataset from RockYou, HaveIbeenPwned, or Kaggle, and clean the data.

- **Step 2: General Analysis** Identifying common password and common lengths and variability of these parameters

- **Step 3: Password pattern** passwords into masks 
    - *e.g* `P@ss123` becomes `C S L L D D D` (Capital, Special, Lower, Lower, Digit...). 
    then analyse masking patterns that are most frequent in the password data

- **Step 4: Semantic decomposition** 
    - **Dictionary lookup:** finding common words that may appear in password, e.g: password, [city name], etc...
    - **Word classification:** categorizing found words into linguistic types (names, nouns, verbs, adjectives, places, dates, etc.) to identify which categories appear most frequently in passwords
    - **L33t detection:** reverse common numerical symbols used for alphabetical substitution, e.g: 3 would be E or e, 4 would be A or a, etc...
    - **Keyboard patterns:** check for pattern that already exist on keyboard: e.g: "qwerty" or "123poiuy"
    - **Pattern type ranking:** analyze and rank the most common pattern categories found, creating a tiered system where more frequent = more predictable

### Phase 2: Predictability
Now that we have some solid understanding on the data and its patterns, and overall probabilistic outcome we want to build a system that can grade our password or predict them 

- **Step 5: Probabilistic prediction** we want to look at the transition probability from character to character to see the likelihood of the next character based on the knowledge of existing one, think of an n-gram LM but instead of word by word its character by character 

- **Step 6: grading** With the above probabilistic prediction calculator, and also adding another script that notices common general patterns we can start grading and punishing users on their password input: 
    - **Pattern type penalties:** apply a weighted deduction system based on pattern type rankings from Step 4 - the more common the pattern category (names, nouns, common verbs), the more points deducted
    - **Specific pattern penalties:** e.g: if user does common pattern: "asdf" or [putting ! at end of a password] -10points, more common the pattern more points removed
    - **Predictability scoring:** the more predictable the characters are based on previous entry the lower the base grade
    - **Combined scoring:** final grade = base predictability score - pattern type penalties - specific pattern penalties + complexity/length bonuses

### Phase 3: password creation and attacking
While we have data and a grading system for password, now we can start making them. 

- **Step 7: creation** Create a script that based on all info and resources available can create passwords, we can feed it passwords we want, or elements we want and have it also edit them to become secure. The generator will incorporate knowledge of common pattern types to avoid them when creating strong passwords.

- **Step 8: Attack simulation** in similar fashion we can make a different script that uses the data we have collected, as well as **some** context fed into the creation script, to simulate a pattern based and spear phishing attack. The attack script now combines our ranked pattern seeds with the same `english-words` dictionary library used in earlier analysis steps, so the cracking run can test both project-specific patterns and a broader English word list. It will still prioritize the most common pattern types first (names, then nouns, etc.) based on our ranking from Phase 1 and record which passwords get cracked and in how many attempts.

- **Step 9: final analysis** if any of the password get cracked, we can use them and the number of attempt it took to analyse what kind of parameters made them more susceptible, was it length? simplicity? certain common words or patterns? We'll specifically analyze which pattern types proved most vulnerable and validate our grading weightings against actual cracking success rates.

```mermaid
graph TD
    %% Styling
    classDef phase1 fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef phase2 fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef phase3 fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef data fill:#f9fbe7,stroke:#827717,stroke-width:1px

    %% Data Sources
    DataSources[("Password Datasets<br/>RockYou, HIBP, Kaggle")]:::data

    %% PHASE 1: Structural Analysis
    subgraph Phase1 ["PHASE 1: Structural Analysis"]
        direction TB
        A1["Step 1: Data Acquisition & Cleaning<br/>Deduplication, filtering, normalization"]:::phase1
        A2["Step 2: General Analysis<br/>Length distribution<br/>Common passwords<br/>Character composition"]:::phase1
        A3["Step 3: Pattern Analysis<br/>Character masks (C,S,L,D)<br/>Frequent mask patterns"]:::phase1
        A4["Step 4: Semantic Decomposition & Classification<br/>Dictionary lookup<br/>Word classification (names, nouns, verbs, etc.)<br/>L33t conversion<br/>Keyboard patterns<br/>Pattern type ranking & tiering"]:::phase1
        PatternDB[("Pattern Database<br/>Masks, words, patterns,<br/>pattern type rankings")]:::data
    end

    %% PHASE 2: Predictability & Grading
    subgraph Phase2 ["PHASE 2: Predictability & Grading"]
        direction TB
        B1["Step 5: Probabilistic Prediction<br/>Character n-gram model<br/>Transition probabilities<br/>Next char likelihood"]:::phase2
        B2["Step 6: Password Grading<br/>Pattern penalties (type-weighted)<br/>Specific pattern penalties<br/>Predictability scoring<br/>Length/complexity bonus<br/>Combined weighted scoring"]:::phase2
        GradedPass[("Graded Password Database")]:::data
    end

    %% PHASE 3: Creation & Attack
    subgraph Phase3 ["PHASE 3: Creation & Attack"]
        direction TB
        C1["Step 7: Password Creation<br/>Template generation<br/>Pattern type avoidance<br/>Security hardening"]:::phase3
        C2["Step 8: Attack Simulation<br/>Pattern type priority attacks<br/>Spear phishing context<br/>Attempt tracking"]:::phase3
        C3[("Cracking Results<br/>Success rates, attempts,<br/>vulnerable pattern types")]:::data
        C4["Step 9: Final Analysis<br/>Length vs crackability<br/>Pattern type susceptibility<br/>Word impact<br/>Grading weight validation"]:::phase3
        Report["Security Report<br/>Findings & recommendations<br/>Pattern type risk tiers"]:::phase3
    end

    %% MAIN FLOW
    DataSources --> A1
    A1 --> A2 & A3 & A4
    A2 & A3 & A4 --> PatternDB
    
    PatternDB --> B1
    B1 --> B2
    PatternDB --> B2
    B2 --> GradedPass
    
    PatternDB --> C1 & C2
    GradedPass --> C1 & C2
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> Report

    %% FEEDBACK LOOPS
    Report -.->|Pattern type rankings<br/>Grading weight feedback| PatternDB
    Report -.->|Attack insights| C1

    %% Legend
    subgraph Legend ["Legend"]
        direction LR
        L1[Phase 1: Structural Analysis]:::phase1
        L2[Phase 2: Predictability]:::phase2
        L3[Phase 3: Creation & Attack]:::phase3
        L4[Data Storage]:::data
    end
```

---
### Credits:

the data originates from the RockYou2024.txt, which has then been cleanup and provided by **BwandoWando** on kaggle at : **https://www.kaggle.com/discussions/accomplishments/519395**
