# Tournament Feature Implementation Plan

## Overview
Add a new "Tournament" tab to RLBotGUI that allows users to create tournament brackets, add bots/humans to a pool, form teams, and run matches through a tournament structure. **Supports 1v1, 2v2, 3v3, and 4v4 team sizes.**

## Current Architecture Analysis

### Existing Patterns to Leverage
1. **Tab Structure**: The app uses Vue Router with 3 routes (`/`, `/sandbox`, `/story`) - see [`main.js`](rlbot_gui/gui/js/main.js:13-17)
2. **Story Mode Pattern**: Story mode demonstrates a complex multi-screen feature with state management, match launching, and result tracking - see [`story-mode.js`](rlbot_gui/gui/js/story-mode.js) and [`story_runner.py`](rlbot_gui/story/story_runner.py)
3. **Bot Pool Management**: [`bot-pool-vue.js`](rlbot_gui/gui/js/bot-pool-vue.js) provides reusable bot selection UI
4. **Match Launching**: [`match_runner.py`](rlbot_gui/match_runner/match_runner.py) handles match creation and execution
5. **State Persistence**: Story mode uses `QSettings` for save/load - see [`story_runner.py`](rlbot_gui/story/story_runner.py:46-78)
6. **Team Configuration**: Match runner already handles team assignments - see how it assigns bots to teams 0 and 1

## Implementation Approach

### 1. Frontend Components (JavaScript/Vue)

#### New Route
- Add `/tournament` route to [`main.js`](rlbot_gui/gui/js/main.js:13-17)
- Add "Tournament" button in main navbar (similar to Story Mode button at [`main-vue.js:58-62`](rlbot_gui/gui/js/main-vue.js:58-62))

#### Tournament Vue Component (`tournament-vue.js`)
Main component with sub-components:
- **Tournament Setup Screen**: Create tournament, name it, select format, **select team size**
- **Team Management Screen**: Assign participants to teams before bracket generation
- **Tournament Bracket View**: Visual bracket display, match results
- **Participant Pool**: Reuse `bot-pool-vue.js` component for adding bots/humans

#### Key Features
1. **Tournament Creation**
   - Tournament name input
   - **Team size selection: 1v1, 2v2, 3v3, 4v4**
   - Format selection: Single Elimination, Double Elimination, Round Robin
   - **Participant count auto-adjustment based on team size** (e.g., 2v2 with 8 teams = 16 participants)

2. **Team Formation**
   - **Auto-generate teams from participant pool based on team size**
   - **Manual team assignment with drag-and-drop**
   - **Team naming support (Team A, Team B, or custom names)**
   - **Random team assignment option**
   - **Team balance indicator (for competitive play)**

3. **Participant Management**
   - Seed participants manually or randomly
   - Visual pool list with drag-to-reorder for seeding
   - **Team assignment phase before bracket generation**

4. **Bracket Generation**
   - Auto-generate bracket based on format and team count
   - Display matches in bracket tree format (showing teams, not individuals)
   - Click match to start it

5. **Match Execution**
   - Reuse existing match launching infrastructure
   - **Assign team members to appropriate side slots (teams 0 and 1)**
   - Display current match participants (team-by-team view)
   - Show match result (win/loss/draw)
   - Auto-advance winning team to next round

6. **Tournament State Persistence**
   - Save/load tournament state using QSettings (pattern from story_runner.py)
   - Resume interrupted tournaments

### 2. Backend Components (Python)

#### New Module: `rlbot_gui/tournament/tournament_runner.py`
Similar to `story_runner.py`, expose Eel functions:
- `tournament_new(name, format, team_size, participants)` - Create new tournament
- `tournament_form_teams(participants, team_size, assignment_method)` - Form teams from participants
- `tournament_load()` - Load existing tournament
- `tournament_save()` - Save tournament state
- `tournament_delete()` - Delete tournament
- `tournament_start_match(match_id)` - Start a specific match
- `tournament_record_result(match_id, winner)` - Record match result and advance

#### Data Structures
```python
class TournamentState:
    name: str
    format: str  # 'single_elimination', 'double_elimination', 'round_robin'
    team_size: int  # 1, 2, 3, or 4
    teams: List[Team]  # List of teams with their members
    matches: List[Match]
    current_round: int
    completed: bool
    winner: Team | None

class Team:
    id: str
    name: str  # Optional custom name
    participants: List[dict]  # Bot/human config (team_size length)
    wins: int
    losses: int
    points: int  # For round robin

class Match:
    id: str
    round: int
    team1: Team | None
    team2: Team | None
    winner: Team | None
    score: tuple | None  # (score_team1, score_team2)
    completed: bool
    byes: bool  # Whether this match has a bye
```

### 3. Team Formation & Bracket Generation Logic

#### Team Size Options
| Team Size | Min Teams | Recommended Teams | Total Participants |
|-----------|-----------|-------------------|-------------------|
| 1v1 | 2 | 4, 8, 16, 32 | 2, 4, 8, 16, 32, 64 |
| 2v2 | 2 | 4, 8, 16 | 4, 8, 16, 32 |
| 3v3 | 2 | 4, 8, 16 | 6, 12, 24, 48 |
| 4v4 | 2 | 4, 8, 16 | 8, 16, 32, 64 |

#### Single Elimination
- Standard bracket: 2^n teams
- Winners advance, losers eliminated
- **Byes for non-power-of-2 team counts**
- **Each match involves team_size * 2 participants**

#### Double Elimination
- Winners bracket and losers bracket
- Losers bracket winner plays winners bracket winner in finals
- More complex bracket generation needed
- **Track which teams are in winners vs losers bracket**

#### Round Robin
- Every team plays every other team once
- **Track individual participant stats within teams**
- Rank by team points, then tiebreakers

## File Structure to Create

```
rlbot_gui/
├── tournament/
│   ├── __init__.py
│   ├── tournament_runner.py      # Backend logic
│   ├── bracket_generator.py      # Bracket generation algorithms
│   ├── team_manager.py           # Team formation logic
│   └── tournament_state.py       # Data classes
└── gui/
    └── js/
        └── tournament-vue.js     # Main tournament component
```

## UI Mockup Description

### Main Tournament Tab (With Team Display)
```
+----------------------------------------------------------+
|  Tournament                                  [Back] [Menu]|
+----------------------------------------------------------+
|                                                            |
|  [ Summer Cup - 2v2 ]                                      |
|                                                            |
|  +----------------+  +----------------+  +----------------+|
|  |   Quarter      |  |    Semi        |  |    Final       ||
|  |   Finals       |  |    Finals      |  |                ||
|  |                |  |                |  |                ||
|  |  Team A vs     |  |  Winner vs     |  |  Winner vs     ||
|  |  Team B        |  |  Winner        |  |  Winner        ||
|  |  [Bot1, Bot2]  |  |                |  |                ||
|  |  [Bot3, Bot4]  |  |                |  |                ||
|  |                |  |                |  |                ||
|  +----------------+  +----------------+  +----------------+|
|                                                            |
|  [New Tournament] [Load] [Export Bracket]                  |
|                                                            |
+----------------------------------------------------------+
```

### Tournament Creation Modal (With Team Size)
```
+----------------------------------+
|  Create Tournament               |
+----------------------------------+
|  Name: [Summer Cup_______]       |
|                                  |
|  Format:                         |
|  ( ) Single Elimination          |
|  ( ) Double Elimination          |
|  ( ) Round Robin                 |
|                                  |
|  Team Size:                      |
|  [1v1] [2v2] [3v3] [4v4]        |
|                                  |
|  Teams: 4                        |
|  (Auto-adjusts based on format)  |
|                                  |
|  [Add from Pool] [Clear All]     |
|                                  |
|  [Participants List:]            |
|  1. [Bot A              ] [x]    |
|  2. [Bot B              ] [x]    |
|  3. [Bot C              ] [x]    |
|  4. [Bot D              ] [x]    |
|  ... (8 participants for 2v2 x 4 teams)
|                                  |
|  [Form Teams] [Cancel]           |
+----------------------------------+
```

### Team Formation Modal
```
+----------------------------------+
|  Form Teams                      |
+----------------------------------+
|  Team Size: 2v2                  |
|  Total Teams: 4                  |
|  Total Participants: 8           |
|                                  |
|  Assignment Method:              |
|  (o) Random                      |
|  ( ) Manual                      |
|  ( ) Seed by Rank (if available) |
|                                  |
|  Team 1:                         |
|    [Bot A              ] [x]     |
|    [Bot B              ] [x]     |
|                                  |
|  Team 2:                         |
|    [Bot C              ] [x]     |
|    [Bot D              ] [x]     |
|                                  |
|  Team 3:                         |
|    [Bot E              ] [x]     |
|    [Bot F              ] [x]     |
|                                  |
|  Team 4:                         |
|    [Bot G              ] [x]     |
|    [Bot H              ] [x]     |
|                                  |
|  [Swap: Bot A <-> Bot C]         |
|  [Clear Teams] [Randomize]       |
|                                  |
|  [Generate Bracket] [Cancel]     |
+----------------------------------+
```

## Integration Points

### With Existing Code
1. **Bot Selection**: Reuse `bot-pool-vue.js` and `bot-card-vue.js`
2. **Match Launching**: Use existing `eel.start_match()` infrastructure - **passes team configurations**
3. **Packet Reading**: Reuse packet translation for determining match winners - **team-based scoring**
4. **Settings Persistence**: Use `QSettings` pattern from story mode
5. **Team Slot Assignment**: Use existing team slot mapping (slots 0-3 = team 0, slots 4-7 = team 1)

### New Dependencies
- None - uses existing BootstrapVue for UI components

## Edge Cases to Handle

1. **Odd participant counts for team size**: 
   - Cannot form full teams → show error with "X participants missing"
   - Allow byes at team level, not participant level
   
2. **Tournament interruption**: Save state frequently, allow resume
   
3. **Human participants**: 
   - **Track which human is assigned to which team slot**
   - **Multi-human tournaments need slot assignment UI**
   
4. **Concurrent matches**: Should only run one match at a time in tournament

5. **Team balance**: For competitive play, provide balance indicator (e.g., average bot rating per team)

6. **Mixed participant types**: Bots and humans in same team - handled by team formation

## Testing Strategy

1. **Unit tests**: 
   - Team formation algorithms
   - Bracket generation algorithms (for each team size)
   - Byes calculation

2. **Integration tests**: 
   - Tournament flow from creation to completion
   - Team-based match launching
   - State persistence across different team sizes

3. **Manual testing**: 
   - All team sizes (1v1, 2v2, 3v3, 4v4)
   - Various team counts
   - Mixed bot/human teams

## MVP Scope Summary

**Feature**: Single elimination tournament bracket with team size support

**Files to Create**:
- `rlbot_gui/tournament/__init__.py`
- `rlbot_gui/tournament/tournament_runner.py`
- `rlbot_gui/tournament/bracket_generator.py`
- `rlbot_gui/tournament/team_manager.py`
- `rlbot_gui/tournament/tournament_state.py`
- `rlbot_gui/gui/js/tournament-vue.js`

**Files to Modify**:
- `rlbot_gui/gui/js/main.js` - Add tournament route
- `rlbot_gui/gui/main.html` - Update keep-alive if needed
- `rlbot_gui/gui/js/main-vue.js` - Add Tournament button to navbar

**Key Integration Points**:
- Reuse `bot-pool-vue.js` for participant selection
- Reuse `eel.start_match()` for match execution - **with team slot assignments**
- Reuse `QSettings` pattern from story mode for persistence
- Reuse packet translation for determining winners - **team-based**

**Estimated Effort**: Moderate - approximately 4-6 days for a developer familiar with the codebase (extra day for team management complexity)

**Risks**:
- Bracket visualization complexity may be underestimated
- Edge cases with odd participant counts for team sizes
- State persistence and recovery from crashes
- **Team slot assignment for human players**

## Recommended Implementation Order

1. **Phase 1: MVP (Single Elimination, 1v1)**
   - Basic tournament creation
   - Single elimination bracket generation
   - Add participants from pool
   - Start matches, record winners
   - Advance to next round
   - Declare tournament winner
   - Auto-save on match result

2. **Phase 2: Team Size Support**
   - **Team formation UI and logic**
   - **Support 2v2, 3v3, 4v4 team sizes**
   - **Team-based bracket display**
   - **Team slot assignment for matches**

3. **Phase 3: Enhanced Features**
   - Round robin format
   - Double elimination format
   - Better bracket visualization
   - Export/import tournament

4. **Phase 4: Polish**
   - Tournament templates
   - Statistics tracking
   - Shareable tournament files
   - Team balance indicators

## Design Decisions (Confirmed)

1. **MVP Scope**: Single elimination only, starting with 1v1
2. **Team Size Progression**: Add 2v2, 3v3, 4v4 in Phase 2
3. **Draw handling**: Rocket League overtime handles draws naturally; no special handling needed unless server error occurs
4. **Human participants**: **Track team slot assignments** (single slot at a time for multi-player humans)
5. **Save behavior**: Auto-save on every match result
6. **Bracket visualization**: Custom simple implementation first, showing team names/members
7. **Team Formation**: Manual or automatic before bracket generation

## Next Steps

1. Begin implementation with Phase 1 (1v1 single elimination)
2. Add team size support (2v2, 3v3, 4v4) in Phase 2
3. Add round robin and double elimination in future iterations

## Tournament Mutator Values Reference

For future implementation of custom mutator settings in tournaments, use these valid values from RLBot:

### Match Length
- `'5 Minutes'`
- `'10 Minutes'`
- `'20 Minutes'`
- `'Unlimited'`

### Max Score
- `'Unlimited'`
- `'1 Goal'`
- `'3 Goals'`
- `'5 Goals'`

### Overtime
- `'Unlimited'`
- `'+5 Max, First Score'`
- `'+5 Max, Random Team'`

### Series Length
- `'Unlimited'`
- `'3 Games'`
- `'5 Games'`
- `'7 Games'`

### Game Speed
- `'Default'`
- `'Slo-Mo'`
- `'Time Warp'`

### Boost Amount
- `'Default'`
- `'Unlimited'`
- `'Recharge (Slow)'`
- `'Recharge (Fast)'`
- `'No Boost'`

### Rumble
- `'None'`
- `'Default'`
- `'Slow'`
- `'Civilized'`
- `'Destruction Derby'`
- `'Spring Loaded'`
- `'Spikes Only'`
- `'Spike Rush'`

### Ball Max Speed
- `'Default'`
- `'Slow'`
- `'Fast'`
- `'Super Fast'`

### Ball Type
- `'Default'`
- `'Cube'`
- `'Puck'`
- `'Basketball'`

### Ball Weight
- `'Default'`
- `'Light'`
- `'Heavy'`
- `'Super Light'`

### Ball Size
- `'Default'`
- `'Small'`
- `'Large'`
- `'Gigantic'`

### Ball Bounciness
- `'Default'`
- `'Low'`
- `'High'`
- `'Super High'`

### Gravity
- `'Default'`
- `'Low'`
- `'High'`
- `'Super High'`

### Demolish
- `'Default'`
- `'Disabled'`
- `'Friendly Fire'`
- `'On Contact'`
- `'On Contact (FF)'`

### Respawn Time
- `'3 Seconds'`
- `'2 Seconds'`
- `'1 Second'`
- `'Disable Goal Reset'`

### Existing Match Behavior
- `'Restart If Different'`
- `'Restart'`
- `'Continue And Spawn'`

## Implementation Notes & Changes from Plan

During implementation, the following deviations from the original plan were made:

### UI Changes
1. **Simplified Match Display**: Changed from stacked participant/score layout to inline "Bot1 vs Bot2" with score below for better readability
2. **Removed Participants Panel**: The participants panel was removed from the active tournament view to give more space for the bracket display
3. **Dynamic Round Naming**: Rounds are now named based on their position from the end (Quarter-Finals, Semi-Finals, Finals) instead of just "Round X"
4. **No Add/Remove Participants Mid-Tournament**: To prevent issues with bracket integrity, participants can only be added during tournament creation, not during an active tournament
5. **Team Formation Phase Added**: Separate screen for team formation before bracket generation

### Bug Fixes
1. **Premature Tournament Completion**: Fixed `is_tournament_final_match()` to check `next_match_id is None` instead of counting active matches
2. **Incorrect Bye Handling**: Fixed `advance_winner()` to only auto-complete byes in round 1, not in later rounds
3. **Score Ordering**: Fixed score recording to preserve team order (team 0 = participant1, team 1 = participant2) instead of sorting by winner
4. **Frontend State Refresh**: Changed polling to fetch fresh state from backend on each iteration instead of using stale references
5. **Infinite Alert Loop**: Removed alert on tournament completion since the winner is already displayed in the header
6. **Team Size Validation**: Added validation to ensure participant count is divisible by team size before forming teams

### Technical Improvements
1. **Automatic Match Launching**: Matches now launch automatically when clicking on a bracket match (similar to story mode)
2. **Automatic Winner Detection**: The backend automatically detects match results and records winners based on team scores
3. **Improved Polling**: Frontend polls for match completion and updates the UI automatically
4. **Team Slot Assignment**: Match launcher now correctly assigns team members to appropriate slot ranges (0-3 for team 0, 4-7 for team 1)
5. **Team Name Support**: Added optional custom team names for better tournament presentation

### Team Size Specific Considerations
1. **Slot Mapping**: RLBot supports up to 8 participants per match (4 per team max)
2. **Human Slot Assignment**: For multi-human teams, need to track which human plays which slot
3. **Team Balance**: Consider implementing a simple "team strength" calculation based on bot difficulty ratings
4. **Bye Handling**: Byes should be at team level, not participant level
5. **Minimum Teams**: All team sizes support minimum 2 teams (4-32 participants depending on size)