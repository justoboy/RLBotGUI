# Double Elimination Losers Bracket Debug Specification

## Part 1: Root Cause Summary (For Engineer Observation)

**Observed Behavior:** For a 9-participant tournament (16-slot bracket), the Losers Bracket fails after initial rounds with participants becoming stuck in uncompletable byes.

**Key Observation from Section 7:**

| LB Round | Matches | Observed Participants | Expected Participants                              |
|----------|---------|-----------------------|----------------------------------------------------|
| LB R1    | 1       | 1 (bye)               | 1 (bye - correct)                                  |
| LB R2    | 2       | 4                     | 5 (4 WB R2 losers + 1 LB R1 bye)                   |
| LB R3    | 1       | 2                     | 5 (2 LB R2 winners + 1 LB R2 bye + 2 WB R3 losers) |
| LB R4    | 1       | 2                     | 3 (2 LB R3 winners + 1 LB R3 bye)                  |
| LB R5    | 1       | 0                     | 2 (1 LB R4 winner + 1 LB R4 bye)                   |
| LB R6    | 1       | 1                     | 2 (1 LB R5 winner + 1 WB Finals loser)             |
| LB R7    | 1       | 1                     | 2 (1 LB R6 winner + 1 WB Finals winner)            |

**Root Cause Hypothesis:** The expected participant counts in the table above appear to be based on an incorrect understanding of the bracket structure. For 9 participants:
- WB R1 has 8 matches (1 actual match + 7 byes), producing only 1 loser
- LB R1 should have 1 match with 1 participant (bye) - this is CORRECT
- LB R2 should receive: 1 (LB R1 winner) + 1 (WB R1 loser) = 2 participants → 1 match

The observed LB R2 having 2 matches with 4 participants suggests the bracket generation is creating too many LB matches, or the expected values in the table are incorrect.

**Primary Suspect:** The LB round calculation at lines 482-496 in `bracket_generator.py` uses `wb_losers_by_round` which is populated AFTER `_process_bye_winners`. This may cause incorrect match counts if bye winners are not properly accounted for.

---

## Part 2: Technical Blueprint for Code Repair

### 1. Data Structures

#### Match Dataclass
Location: [`tournament_state.py`](rlbot_gui/tournament/tournament_state.py:79-135)

```python
@dataclass
class Match:
    match_id: str
    round_num: int
    participant1: Optional[Participant]
    participant2: Optional[Participant]
    completed: bool
    winner: Optional[Participant] = None
    next_match_id: Optional[str] = None  # Where winner advances
    loser_next_match_id: Optional[str] = None  # Where loser drops (WB to LB)
```

#### TournamentState Dataclass
Location: [`tournament_state.py`](rlbot_gui/tournament/tournament_state.py:138-200)

```python
@dataclass
class TournamentState:
    matches: List[Match]  # WB matches + Grand Final
    losers_bracket_matches: List[Match]  # LB matches only
    team_size: int
    teams: Optional[List[Team]] = None
```

---

### 2. Losers Bracket Generation Algorithm

Location: [`bracket_generator.py`](rlbot_gui/tournament/bracket_generator.py:446-520)

#### 2.1 Calculate WB Losers by Round
```python
# Count actual losers from each WB round (only matches with 2 participants)
wb_losers_by_round: Dict[int, int] = {}
for m in winners_matches:
    if m.round_num not in wb_losers_by_round:
        wb_losers_by_round[m.round_num] = 0
    if m.participant1 is not None and m.participant2 is not None:
        wb_losers_by_round[m.round_num] += 1
```

#### 2.2 Calculate Number of LB Rounds
```python
num_lb_rounds = 2 * num_rounds - 2
# For 16-slot bracket (num_rounds=4): num_lb_rounds = 6
```

#### 2.3 Create LB Matches by Round
```python
for lb_round_num in range(1, num_lb_rounds + 1):
    if lb_round_num == 1:
        # LB R1: losers from WB R1
        losers_from_wb_r1 = wb_losers_by_round.get(1, 0)
        num_lb_matches = math.ceil(losers_from_wb_r1 / 2) if losers_from_wb_r1 > 0 else 0
    elif lb_round_num % 2 == 1:
        # Odd round (3, 5, ...): winners from previous LB round play each other
        prev_round_matches = len(lb_by_round.get(lb_round_num - 1, []))
        num_lb_matches = math.ceil(prev_round_matches / 2) if prev_round_matches > 0 else 0
    else:
        # Even round (2, 4, 6, ...): winners from previous LB + losers from WB
        prev_round_matches = len(lb_by_round.get(lb_round_num - 1, []))
        wb_round_for_losers = (lb_round_num // 2) + 1  # LB R2 -> WB R2, LB R4 -> WB R3
        losers_from_wb = wb_losers_by_round.get(wb_round_for_losers, 0)
        total_participants = prev_round_matches + losers_from_wb
        num_lb_matches = math.ceil(total_participants / 2) if total_participants > 0 else 0
    
    # Edge case: ensure at least 1 match if there are participants
    if num_lb_matches < 1 and (lb_round_num == 1 or len(lb_by_round.get(lb_round_num - 1, [])) > 0 or wb_losers_by_round.get((lb_round_num // 2) + 1, 0) > 0):
        num_lb_matches = 1
```

**Critical Note:** The formula `wb_round_for_losers = (lb_round_num // 2) + 1` maps:
- LB R2 → WB R2
- LB R4 → WB R3
- LB R6 → WB R4

But WB R1 losers should feed into LB R1, and LB R2 should receive LB R1 winners + any remaining WB R1 losers (if LB R1 didn't have capacity for all WB R1 losers).

---

### 3. LB Internal Linking (Winner Advancement)

Location: [`bracket_generator.py`](rlbot_gui/tournament/bracket_generator.py:557-616)

#### 3.1 Link LB R1 to LB R2
```python
if 1 in lb_by_round and 2 in lb_by_round:
    lb_round1_matches = lb_by_round[1]
    lb_round2_matches = lb_by_round[2]
    for i, lb_match in enumerate(lb_round1_matches):
        if i < len(lb_round2_matches):
            lb_match.next_match_id = lb_round2_matches[i].match_id
```

#### 3.2 Link LB Round 2+ to Subsequent Rounds
```python
for lb_round_num in range(2, num_lb_rounds):
    lb_round_matches = lb_by_round[lb_round_num]
    next_lb_round_matches = lb_by_round.get(lb_round_num + 1, [])
    
    if len(lb_round_matches) == 1:
        # Single match: winner advances to next round
        if next_lb_round_matches:
            lb_round_matches[0].next_match_id = next_lb_round_matches[0].match_id
    else:
        if lb_round_num % 2 == 1:
            # Odd round: winners advance one-to-one to next round (even round)
            for i, lb_match in enumerate(lb_round_matches):
                if i < len(next_lb_round_matches):
                    lb_match.next_match_id = next_lb_round_matches[i].match_id
        else:
            # Even round: pair consecutive matches, winners play in next odd round
            for i in range(0, len(lb_round_matches), 2):
                if i + 1 < len(lb_round_matches):
                    next_match_idx = i // 2
                    if next_match_idx < len(next_lb_round_matches):
                        lb_round_matches[i].next_match_id = next_lb_round_matches[next_match_idx].match_id
                        lb_round_matches[i+1].next_match_id = next_lb_round_matches[next_match_idx].match_id
                elif i < len(lb_round_matches):
                    # Odd number of matches: last match's winner advances
                    next_match_idx = i // 2
                    if next_match_idx < len(next_lb_round_matches):
                        lb_round_matches[i].next_match_id = next_lb_round_matches[next_match_idx].match_id

# Link LB Finals winner to Grand Final
lb_finals_match.next_match_id = grand_final_id
```

---

### 4. WB to LB Loser Linking

Location: [`bracket_generator.py`](rlbot_gui/tournament/bracket_generator.py:618-727)

#### 4.1 Link WB R1 Losers to LB R1
```python
if 1 in wb_by_round and 1 in lb_by_round:
    wb_round1_matches = wb_by_round[1]
    lb_round1_matches = lb_by_round[1]
    
    # Filter to only matches with both participants (actual matches, not byes)
    actual_wb_r1_matches = [m for m in wb_round1_matches 
                            if m.participant1 is not None and m.participant2 is not None]
    
    # Pair losers: loser of WB match 0 and 1 go to LB match 0, etc.
    for i, lb_match in enumerate(lb_round1_matches):
        wb_match_idx1 = i * 2
        wb_match_idx2 = i * 2 + 1
        if wb_match_idx1 < len(actual_wb_r1_matches):
            actual_wb_r1_matches[wb_match_idx1].loser_next_match_id = lb_match.match_id
        if wb_match_idx2 < len(actual_wb_r1_matches):
            actual_wb_r1_matches[wb_match_idx2].loser_next_match_id = lb_match.match_id
```

#### 4.2 Link WB Round N (N >= 2) Losers to LB Round (2*N - 2)
```python
for wb_round in range(2, num_rounds):
    if wb_round in wb_by_round:
        wb_matches = wb_by_round[wb_round]
        actual_wb_matches = [m for m in wb_matches 
                            if m.participant1 is not None and m.participant2 is not None]
        
        lb_round_num = 2 * wb_round - 2  # WB R2 -> LB R2, WB R3 -> LB R4
        if lb_round_num in lb_by_round:
            lb_matches = lb_by_round[lb_round_num]
            prev_lb_matches = lb_by_round.get(lb_round_num - 1, [])
            
            lb_match_idx = 0
            wb_match_idx = 0
            
            # First pass: pair LB previous round winners with WB losers
            for i, prev_lb_match in enumerate(prev_lb_matches):
                if wb_match_idx < len(actual_wb_matches) and lb_match_idx < len(lb_matches):
                    actual_wb_matches[wb_match_idx].loser_next_match_id = lb_matches[lb_match_idx].match_id
                    wb_match_idx += 1
                    lb_match_idx += 1
            
            # Second pass: pair remaining WB losers with each other
            while wb_match_idx < len(actual_wb_matches):
                if lb_match_idx < len(lb_matches):
                    actual_wb_matches[wb_match_idx].loser_next_match_id = lb_matches[lb_match_idx].match_id
                    wb_match_idx += 1
                    
                    if wb_match_idx < len(actual_wb_matches):
                        actual_wb_matches[wb_match_idx].loser_next_match_id = lb_matches[lb_match_idx].match_id
                        wb_match_idx += 1
                    
                    lb_match_idx += 1
```

#### 4.3 Link WB Finals Loser to LB Finals
```python
for m in winners_matches:
    if m.next_match_id is None:  # WB Finals
        m.next_match_id = grand_final_id  # Winner goes to Grand Final
        if num_lb_rounds > 0 and num_lb_rounds in lb_by_round and len(lb_by_round[num_lb_rounds]) > 0:
            m.loser_next_match_id = lb_finals_id  # Loser goes to LB Finals
```

---

### 5. Bye Handling in Losers Bracket

Location: [`bracket_generator.py`](rlbot_gui/tournament/bracket_generator.py:743-744)

```python
# Process bye winners in the losers bracket
_process_bye_winners(losers_matches)
```

Location: [`bracket_generator.py`](rlbot_gui/tournament/bracket_generator.py:498-500)

```python
# Ensure at least 1 match if there are any participants
if num_lb_matches < 1 and (lb_round_num == 1 or len(lb_by_round.get(lb_round_num - 1, [])) > 0 or wb_losers_by_round.get((lb_round_num // 2) + 1, 0) > 0):
    num_lb_matches = 1
```

---

### 6. Code Locations Reference

| Function                                | File                   | Lines     | Purpose                                    |
|-----------------------------------------|------------------------|-----------|--------------------------------------------|
| `generate_double_elimination_bracket()` | `bracket_generator.py` | 332-746   | Main entry point                           |
| `generate_losers_bracket()`             | `bracket_generator.py` | 446-520   | LB match count calculation                 |
| `_link_lb_matches()`                    | `bracket_generator.py` | 557-616   | LB internal linking                        |
| `_link_wb_losers_to_lb()`               | `bracket_generator.py` | 618-727   | WB to LB loser linking                     |
| `_process_bye_winners()`                | `bracket_generator.py` | N/A       | Process bye winners during generation      |
| `_check_and_handle_lb_bye()`            | `tournament_runner.py` | 1093-1158 | Check and handle LB bye during progression |
| `_populate_losers_bracket_match()`      | `tournament_runner.py` | 1021-1090 | Populate LB match with WB loser            |
| `_get_all_feeders()`                    | `tournament_runner.py` | 1419-1440 | Get feeder matches                         |

---

## 7. Observed Behavior: Losers Bracket with 9 Participants (16-Slot Bracket)

### 7.1 Observed Bracket State

**Tournament Configuration:** 9 participants (uses 16-slot bracket with 7 byes)

**Winners Bracket (Complete):**
- WB R1: 8 matches (1 actual match + 7 byes)
- WB R2: 4 matches
- WB R3: 2 matches
- WB Finals: 1 match

**Observed Losers Bracket State:**

| LB Round | Matches | Observed Participants | Expected Participants                              |
|----------|---------|-----------------------|----------------------------------------------------|
| LB R1    | 1       | 1 (bye)               | 1 (bye - correct)                                  |
| LB R2    | 2       | 4                     | 5 (4 WB R2 losers + 1 LB R1 bye)                   |
| LB R3    | 1       | 2                     | 5 (2 LB R2 winners + 1 LB R2 bye + 2 WB R3 losers) |
| LB R4    | 1       | 2                     | 3 (2 LB R3 winners + 1 LB R3 bye)                  |
| LB R5    | 1       | 0                     | 2 (1 LB R4 winner + 1 LB R4 bye)                   |
| LB R6    | 1       | 1                     | 2 (1 LB R5 winner + 1 WB Finals loser)             |
| LB R7    | 1       | 1                     | 2 (1 LB R6 winner + 1 WB Finals winner)            |

**Key Observation:** The LB has incorrect participant counts starting from LB R2. The bye from LB R1 is not being carried forward to LB R2. Subsequent rounds have cascading errors where participants are missing and byes are not being properly tracked.

**Correct WB to LB Routing:**
- WB R1 losers → LB R1 (creates the 1 bye)
- WB R2 losers → LB R2 (along with LB R1 bye winner)
- WB R3 losers → LB R3 (along with LB R2 winners)
- ...
- WB Finals loser → LB Finals (LB R6 in a 4-round WB)
- LB Finals winner → Grand Final (faces WB Finals winner)