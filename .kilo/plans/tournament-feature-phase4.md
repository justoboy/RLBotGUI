# Tournament Feature Phase 4 Implementation Plan

## Overview
This plan outlines Phase 4 features for the RLBotGUI tournament system, building upon the completed Phase 3 features. Phase 4 introduces new tournament formats, enhanced UX, and improved tournament management capabilities.

## Critical Bug Fix: Human Participant Validation

**Issue**: When adding humans to a tournament, they are not being counted toward the participant total, allowing users to create tournaments with odd participant counts that cannot form full teams. Additionally, humans are not being assigned to any teams during team formation. Human players also cannot enter their usernames.

**Symptoms**:
- User adds 4 bots + 2 humans for a 2v2 tournament (should need 4 participants per team × 2 teams = 8 total, but only 4 bots are counted)
- Team formation fails or creates incomplete teams because humans are ignored
- Validation passes when it should fail (e.g., 3 bots + 1 human for 2v2 = 4 participants, but only 3 are counted)
- No UI to enter human player usernames
- Humans not appearing in team lists after team formation

**Root Cause**: The participant count validation and team formation logic only considers bots, not humans with `participant_type: 'human'`. The human username input UI may also be missing or not properly connected to the participant creation flow.

**Fix Required**:

### 1. Participant Count Validation
- Update `validate_team_formation()` to count all participants regardless of type (bot or human)
- Ensure error messages correctly reflect total participant count including humans

### 2. Human Username Input
- Verify "Human Players" section in tournament creation modal allows entering usernames for each human
- Ensure usernames are stored in participant objects with `participant_type: 'human'`
- Verify human participants are passed to team formation logic

### 3. Team Formation
- Update team formation functions to include humans in the pool for random/seeded/manual assignment
- Humans should be assignable to teams just like bots
- Humans should appear in team lists after formation

### 4. UI Feedback
- Ensure the participant count display shows total participants (bots + humans)
- Verify human participants appear in the participant pool list with their usernames
- Verify humans are displayed in team formation UI

**Files to Investigate/Modify**:
- `rlbot_gui/tournament/team_manager.py` - Fix `validate_team_formation()` and team formation functions
- `rlbot_gui/gui/js/tournament-vue.js` - Verify human username input, participant count display, team formation UI
- `rlbot_gui/tournament/tournament_runner.py` - Verify human participant handling in tournament creation
- `rlbot_gui/gui/tournament-templates/modals.html` - Verify human username input UI exists

**Priority**: **CRITICAL** - This is a blocking bug that prevents proper tournament creation with human participants.

## Current Status Summary

| Phase | Status | Key Features |
|-------|--------|--------------|
| Phase 1 | ✅ Complete | 1v1 single elimination, import/export, basic bracket |
| Phase 2 | ✅ Complete | Team sizes 2v2-5v5, double elimination, round robin, multi-human |
| Phase 3 | ✅ Complete | LAN workflow, templates, statistics, bracket visualization, team balance |
| Phase 4 | ⬜ Planned | Swiss format, auto-start, team names, manual pairing, match history |

---

## Phase 4 Features

### 1. Swiss Tournament Format

**Description**: A non-elimination tournament format where all participants play a fixed number of rounds. Participants are matched against opponents with similar win-loss records each round. Popular in gaming tournaments because everyone stays engaged throughout.

**Key Requirements**:
- **Round count**: Calculated as `log2(participants)` rounded up (e.g., 8 participants = 3 rounds, 16 participants = 4 rounds)
- **Matching algorithm**: Pair participants with similar records (same win count), avoiding rematches when possible
- **Tiebreakers**: User-selectable priority order for ranking participants with same win count:
  - Match score differential (goals for - goals against)
  - Total goals scored
  - Head-to-head result (if participants played each other)
- **Winner determination**: 
  - Primary: Most wins after all rounds
  - Tiebreaker: If top 2 participants tie, schedule a head-to-head playoff match
- **Team support**: Full support for 1v1, 2v2, 3v3, 4v4, 5v5 team formats

**Data Structures**:
```python
@dataclass
class SwissMatch:
    match_id: str
    round_num: int
    participant1: Optional[Participant] = None
    participant2: Optional[Participant] = None
    # Team-based fields
    team1: Optional[Team] = None
    team2: Optional[Team] = None
    winner: Optional[Participant] = None
    winner_team: Optional[Team] = None
    score: Optional[tuple] = None
    completed: bool = False
    tiebreaker_score: float = 0.0  # Calculated from match stats

@dataclass
class SwissTiebreakerSettings:
    primary: str  # 'score_differential', 'goals_scored', 'head_to_head'
    secondary: Optional[str] = None
    tertiary: Optional[str] = None
```

**UI Changes**:
- Add "Swiss" to format selection in tournament creation modal
- Swiss-specific settings panel:
  - Round count (auto-calculated, editable)
  - Tiebreaker priority dropdowns (primary, secondary, tertiary)
- Swiss bracket view:
  - Round-by-round match listing
  - Live standings panel showing current rankings
  - Playoff match indicator when top 2 are tied

**Files to Modify**:
- `rlbot_gui/tournament/bracket_generator.py` - Add `generate_swiss_bracket()`
- `rlbot_gui/tournament/tournament_state.py` - Add Swiss-specific data structures
- `rlbot_gui/tournament/tournament_runner.py` - Add Swiss match scheduling logic
- `rlbot_gui/gui/js/tournament-vue.js` - Add Swiss UI components

---

### 2. Auto-Start Matches

**Description**: Automatic match progression with configurable timer between matches. Ideal for all-bot tournaments or when operator wants hands-off progression.

**Key Requirements**:
- **Timer options**: Predefined intervals (10s, 30s, 60s, 120s)
- **Checkbox toggle**: "Only auto-start matches without humans" (defaults to true)
- **Auto-start behavior**:
  - Auto-start is OFF by default when tournament loads
  - User clicks "Auto-Start" button to enable
  - Countdown begins immediately after previous match ends
  - Clicking "Auto-Start" again cancels countdown and disables
- **Manual override**: Clicking "Start Match" cancels timer and starts immediately
- **Visual feedback**: Countdown timer display, auto-start status indicator

**UI Changes**:
- Auto-start control panel in active tournament view:
  - "Auto-Start" toggle button (off/on states)
  - Timer dropdown (10s, 30s, 60s, 120s)
  - "Only auto-start non-human matches" checkbox
  - Countdown display when active (e.g., "Next match in: 15s")
- Auto-start status badge in match card (e.g., "Auto-starting in 15s")

**Files to Modify**:
- `rlbot_gui/tournament/tournament_runner.py` - Add auto-start timer logic
- `rlbot_gui/gui/js/tournament-vue.js` - Add auto-start UI components

---

### 3. Start Match Button

**Description**: Replace immediate click-to-start with explicit "Start Match" button workflow. Match must be selected first, then user confirms start.

**Key Requirements**:
- **Selection behavior**: Click match to select (visual highlight), only one match selectable at a time
- **Start Match button**: Fixed toolbar button, enabled only when match selected or auto-start disabled
- **Keyboard shortcut**: Enter key starts selected match
- **Default behavior**: Click-to-start replaced entirely (no dual behavior)

**UI Changes**:
- Selected match highlight (border glow or background color)
- Fixed toolbar with "Start Match" button (disabled when no selection)
- Keyboard shortcut indicator (optional tooltip: "Press Enter to start")

**Files to Modify**:
- `rlbot_gui/gui/js/tournament-vue.js` - Add selection state, start match button handler
- `rlbot_gui/gui/css/tournament.css` - Add selected match styling

---

### 4. Random Team Names

**Description**: Generate creative team names by combining descriptors and nouns instead of "Team A, Team B".

**Key Requirements**:
- **Generation timing**: During team formation, with option to re-randomize
- **Custom name override**: Users can edit auto-generated names
- **Name pool**: 100+ combinations (descriptor + noun pattern)
- **Uniqueness**: All team names unique within tournament
- **Pattern**: Descriptor + Noun (e.g., "Blue Eagles", "Raging Bots", "Soaring Ravens")

**Name Pool Structure**:
```python
DESCRIPTORS = ['Blue', 'Red', 'Green', 'Golden', 'Silver', 'Dark', 'Light', 'Raging', 'Soaring', 'Fierce', ...]
NOUNS = ['Eagles', 'Bots', 'Ravens', 'Wolves', 'Tigers', 'Dragons', 'Knights', 'Titans', 'Phantoms', ...]
# 10+ descriptors × 10+ nouns = 100+ combinations
```

**UI Changes**:
- Team formation screen: "Randomize Team Names" button
- Team name fields editable after generation
- Re-randomize option for individual teams or all teams

**Files to Modify**:
- `rlbot_gui/tournament/team_manager.py` - Add `generate_team_names()` function
- `rlbot_gui/gui/js/tournament-vue.js` - Add team name randomization UI

---

### 5. Manual Team Pairing

**Description**: Allow users to manually specify which participants must be on the same team before auto-forming remaining teams.

**Key Requirements**:
- **Pairing mechanism**: Click two participants, then "Pair Together" button
- **Conflict handling**:
  - If participant already paired, move them to new team
  - If team at capacity, show warning and prevent pairing
- **Auto-formation**: After manual pairing, auto-form remaining teams with unpaired participants
- **UI placement**: Separate "Manual Pairing" tab/page in team formation flow

**UI Changes**:
- Team formation screen with tabs: "Random", "Seeded", "Manual Pairing"
- Manual Pairing tab:
  - Participant list with selection state
  - "Pair Selected" button (enabled when 2 participants selected)
  - Visual indication of paired participants
  - "Auto-Form Remaining Teams" button
  - Team size limit warnings

**Files to Modify**:
- `rlbot_gui/tournament/team_manager.py` - Add `pair_participants()` and `form_teams_with_pairs()` functions
- `rlbot_gui/gui/js/tournament-vue.js` - Add manual pairing UI components

---

### 6. Tournament Mutator Presets

**Description**: Quick-select preset mutator configurations for common game modes (Standard, Rumble, Hoops, etc.).

**Key Requirements**:
- **Preset types**: Standard, Rumble, Hoops, Spike Rush, Boomer, Drop Shot, Snow Day, Hockey
- **Single preset per tournament**: Applied to all matches
- **Editable**: Preset loads values into mutator dropdowns, user can adjust individual settings
- **Timing**: Set during tournament creation (mutator settings section)
- **Existing templates**: Templates already support import/export, presets are separate quick-selects

**UI Changes**:
- Tournament creation modal: Mutator settings section
- "Preset" dropdown above mutator fields:
  - Default: "Custom"
  - Options: Standard, Rumble, Hoops, Spike Rush, Boomer, Drop Shot, Snow Day, Hockey
- Selecting preset populates mutator dropdowns with preset values
- User can modify any field after preset selection

**Files to Modify**:
- `rlbot_gui/gui/js/tournament-vue.js` - Add preset dropdown and value population logic
- `rlbot_gui/gui/tournament-templates/` - Add preset definitions (JSON or JS constants)

**Preset Definitions** (example):
```javascript
const MUTATOR_PRESETS = {
  'standard': {
    game_mode: 'Soccer',
    boost_amount: 'Default',
    ball_speed: 'Default',
    // ... all standard settings
  },
  'rumble': {
    game_mode: 'Rumble',
    boost_amount: 'Default',
    // ... rumble-specific settings
  },
  // ... more presets
};
```

---

### 7. Match History View

**Description**: Dedicated view showing all completed matches with scores, stats, and export capability.

**Key Requirements**:
- **Information displayed**:
  - Basic: Teams/players, score, round number, winner
  - Extended (expandable): Match duration, goals/saves/demolitions per player (from packet data)
- **View format**: Grouped by round with expandable sections, chronological within rounds
- **Export**: CSV and JSON formats available
- **Auto-refresh**: View updates automatically when matches complete

**UI Changes**:
- New "Match History" tab in active tournament view
- Round sections (expandable/collapsible)
- Match entries with:
  - Teams and score (always visible)
  - Expand button to show detailed stats
  - Duration timestamp
- Export buttons: "Export CSV", "Export JSON"

**Files to Modify**:
- `rlbot_gui/tournament/tournament_runner.py` - Add `get_match_history()` with stats
- `rlbot_gui/gui/js/tournament-vue.js` - Add match history view component
- `rlbot_gui/gui/tournament-templates/active.html` - Add Match History tab markup

---

### 8. Seeding Editor

**Description**: Visual editor to reorder participants before team formation. Participants are randomly seeded by default, but users can adjust.

**Key Requirements**:
- **Default seeding**: Random on tournament creation
- **Editing mechanism**: Click-to-select then pair (simpler than drag-and-drop)
- **Timing**: After mutator settings, before bracket generation
- **Integration**: Works with manual team pairing feature

**UI Changes**:
- Seeding editor in team formation flow:
  - Participant list with random order
  - Click participant to select, click another to swap positions
  - "Randomize" button to re-shuffle
  - Proceed to team formation or manual pairing

**Files to Modify**:
- `rlbot_gui/gui/js/tournament-vue.js` - Add seeding editor UI

---

### 9. Bye Scheduling (Automatic, Fair)

**Description**: Automatic bye placement for non-power-of-2 participant counts. No user configuration needed - uses standard fair placement.

**Key Requirements**:
- **Applicability**: Single elimination and double elimination only (Swiss and Round Robin don't use byes)
- **Placement**: Top seeds receive byes in first round (standard tournament practice)
- **Fairness**: Ensures top seeds aren't disadvantaged by participant count
- **No UI**: Automatic, no user configuration needed

**Implementation**:
- Existing bracket generation already handles byes
- Verify byes are placed for top seeds (standard bracket seeding)
- Document behavior in tournament creation help text

**Files to Modify**:
- `rlbot_gui/tournament/bracket_generator.py` - Verify bye placement logic

---

## Implementation Order

**Priority Order (as confirmed by user):**

1. **🐛 Bug Fix: Human Participant Validation** - Fix human count not being included in participant total validation, fix humans not being assigned to teams
2. **Random Team Names** - Independent, enhances team formation
3. **Seeding Editor + Manual Team Pairing** - Seeding editor foundation, manual pairing builds on it
4. **Start Match Button + Auto-Start Matches** - Start match button first, auto-start builds on it
5. **Swiss Tournament Format** - Major new format, independent of UX features
6. **Match History View** - Requires match completion data
7. **Tournament Mutator Presets** - Independent, enhances tournament creation

**Bye Scheduling** - Verification only, no implementation needed (automatic fair placement for top seeds)

---

## Files Summary

### New Files
- None (all features extend existing files)

### Modified Files
| File | Changes |
|------|---------|
| `rlbot_gui/tournament/bracket_generator.py` | Add `generate_swiss_bracket()`, verify bye placement |
| `rlbot_gui/tournament/tournament_state.py` | Add Swiss data structures, tiebreaker settings |
| `rlbot_gui/tournament/team_manager.py` | Add `generate_team_names()`, `pair_participants()`, `form_teams_with_pairs()` |
| `rlbot_gui/tournament/tournament_runner.py` | Add Swiss scheduling, auto-start timer, match history |
| `rlbot_gui/gui/js/tournament-vue.js` | Add Swiss UI, auto-start controls, start match button, team names, manual pairing, match history |
| `rlbot_gui/gui/css/tournament.css` | Add selected match styling, Swiss-specific styles |
| `rlbot_gui/gui/tournament-templates/active.html` | Add Match History tab, auto-start controls |
| `rlbot_gui/gui/tournament-templates/modals.html` | Add Swiss settings, seeding editor, manual pairing UI |

---

## Testing Checklist

### Swiss Format
- [ ] Round count calculation (log2 of participants)
- [ ] Matching algorithm (similar records, no rematches)
- [ ] Tiebreaker ranking (all three types)
- [ ] Playoff match when top 2 tied
- [ ] Team sizes 1v1 through 5v5

### Auto-Start
- [ ] Timer countdown display
- [ ] Toggle on/off behavior
- [ ] Human match skip when checkbox enabled
- [ ] Manual override cancels timer
- [ ] Timer intervals (10s, 30s, 60s, 120s)

### Start Match Button
- [ ] Match selection highlight
- [ ] Button enabled/disabled state
- [ ] Enter key shortcut
- [ ] Only one match selectable

### Random Team Names
- [ ] 100+ unique combinations
- [ ] Re-randomize all teams
- [ ] Re-randomize individual team
- [ ] Custom name override
- [ ] Uniqueness enforcement

### Manual Team Pairing
- [ ] Pair two participants
- [ ] Move participant from one pair to another
- [ ] Team capacity warning
- [ ] Auto-form remaining teams

### Mutator Presets
- [ ] All preset types load correctly
- [ ] Values populate mutator dropdowns
- [ ] User can modify preset values
- [ ] Preset selection during creation only

### Match History
- [ ] Round grouping
- [ ] Expandable stats
- [ ] CSV export format
- [ ] JSON export format
- [ ] Auto-refresh on match completion

---

## Open Questions

1. **Swiss rematch avoidance**: Should the algorithm strictly avoid rematches, or allow rematches if no other options exist in late rounds?
   - Recommendation: Strict avoidance preferred, but allow rematch if pool exhausted

2. **Match history detail level**: Which packet-derived stats are most valuable?
   - Recommendation: Goals, saves, assists, demolitions, score contribution

3. **Preset completeness**: Should all RL game modes be included, or just the most popular?
   - Recommendation: Include all standard modes (Soccer, Rumble, Hoops, Spike Rush, Drop Shot, Snow Day, Hockey, Heatseeker)
