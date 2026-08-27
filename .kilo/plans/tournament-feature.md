# Tournament Feature Implementation Plan

## Overview
Add a new "Tournament" tab to RLBotGUI that allows users to create tournament brackets, add bots/humans to a pool, and run matches through a tournament structure.

## Current Architecture Analysis

### Existing Patterns to Leverage
1. **Tab Structure**: The app uses Vue Router with 3 routes (`/`, `/sandbox`, `/story`) - see [`main.js`](rlbot_gui/gui/js/main.js:13-17)
2. **Story Mode Pattern**: Story mode demonstrates a complex multi-screen feature with state management, match launching, and result tracking - see [`story-mode.js`](rlbot_gui/gui/js/story-mode.js) and [`story_runner.py`](rlbot_gui/story/story_runner.py)
3. **Bot Pool Management**: [`bot-pool-vue.js`](rlbot_gui/gui/js/bot-pool-vue.js) provides reusable bot selection UI
4. **Match Launching**: [`match_runner.py`](rlbot_gui/match_runner/match_runner.py) handles match creation and execution
5. **State Persistence**: Story mode uses `QSettings` for save/load - see [`story_runner.py`](rlbot_gui/story/story_runner.py:46-78)

## Implementation Approach

### 1. Frontend Components (JavaScript/Vue)

#### New Route
- Add `/tournament` route to [`main.js`](rlbot_gui/gui/js/main.js:13-17)
- Add "Tournament" button in main navbar (similar to Story Mode button at [`main-vue.js:58-62`](rlbot_gui/gui/js/main-vue.js:58-62))

#### Tournament Vue Component (`tournament-vue.js`)
Main component with sub-components:
- **Tournament Setup Screen**: Create tournament, name it, select format
- **Tournament Bracket View**: Visual bracket display, match results
- **Participant Pool**: Reuse `bot-pool-vue.js` component for adding bots/humans

#### Key Features
1. **Tournament Creation**
   - Tournament name input
   - Format selection: Single Elimination, Double Elimination, Round Robin
   - Participant count auto-adjustment (2, 4, 8, 16, 32)

2. **Participant Management**
   - Seed participants manually or randomly
   - Visual pool list with drag-to-reorder for seeding

3. **Bracket Generation**
   - Auto-generate bracket based on format
   - Display matches in bracket tree format
   - Click match to start it

4. **Match Execution**
   - Reuse existing match launching infrastructure
   - Display current match participants
   - Show match result (win/loss/draw)
   - Auto-advance winners to next round

5. **Tournament State Persistence**
   - Save/load tournament state using QSettings (pattern from story_runner.py)
   - Resume interrupted tournaments

### 2. Backend Components (Python)

#### New Module: `rlbot_gui/tournament/tournament_runner.py`
Similar to `story_runner.py`, expose Eel functions:
- `tournament_new(name, format, participants)` - Create new tournament
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
    participants: List[dict]  # Bot/human config
    matches: List[Match]
    current_round: int
    completed: bool
    winner: dict | None

class Match:
    id: str
    round: int
    participant1: dict | None
    participant2: dict | None
    winner: dict | None
    score: tuple | None  # (score1, score2)
    completed: bool
```

### 3. Bracket Generation Logic

#### Single Elimination
- Standard bracket: 2^n participants
- Winners advance, losers eliminated
- Byes for non-power-of-2 counts

#### Double Elimination
- Winners bracket and losers bracket
- Losers bracket winner plays winners bracket winner in finals
- More complex bracket generation needed

#### Round Robin
- Every participant plays every other
- Track wins/losses/points
- Rank by points, then tiebreakers

## File Structure to Create

```
rlbot_gui/
├── tournament/
│   ├── __init__.py
│   ├── tournament_runner.py      # Backend logic
│   ├── bracket_generator.py      # Bracket generation algorithms
│   └── tournament_state.py       # Data classes
└── gui/
    └── js/
        └── tournament-vue.js     # Main tournament component
```

## UI Mockup Description

### Main Tournament Tab
```
+----------------------------------------------------------+
|  Tournament                                  [Back] [Menu]|
+----------------------------------------------------------+
|                                                            |
|  [ Tournament: Summer Cup ]                                |
|                                                            |
|  +----------------+  +----------------+  +----------------+|
|  |   Quarter      |  |    Semi        |  |    Final       ||
|  |   Finals       |  |    Finals      |  |                ||
|  |                |  |                |  |                ||
|  |  [Bot A]  vs   |  |  [Winner]  vs  |  |  [Winner]  vs  ||
|  |  [Bot B]       |  |  [Winner]      |  |  [Winner]      ||
|  |                |  |                |  |                ||
|  +----------------+  +----------------+  +----------------+|
|                                                            |
|  [Add Participant] [Randomize Seeding] [Export Bracket]   |
|                                                            |
+----------------------------------------------------------+
```

### Tournament Creation Modal
```
+----------------------------------+
|  Create Tournament               |
+----------------------------------+
|  Name: [Summer Cup________]      |
|                                  |
|  Format:                         |
|  ( ) Single Elimination          |
|  ( ) Double Elimination          |
|  ( ) Round Robin                 |
|                                  |
|  Participants: 8                 |
|  [Add from Pool] [Clear All]     |
|                                  |
|  [Participants List:]            |
|  1. [Bot A              ] [x]    |
|  2. [Bot B              ] [x]    |
|  ...                             |
|                                  |
|  [Generate Bracket] [Cancel]     |
+----------------------------------+
```

## Integration Points

### With Existing Code
1. **Bot Selection**: Reuse `bot-pool-vue.js` and `bot-card-vue.js`
2. **Match Launching**: Use existing `eel.start_match()` infrastructure
3. **Packet Reading**: Reuse packet translation for determining match winners
4. **Settings Persistence**: Use `QSettings` pattern from story mode

### New Dependencies
- None - uses existing BootstrapVue for UI components

## Edge Cases to Handle

1. **Odd participant counts**: Byes in first round for single elimination
2. **Tournament interruption**: Save state frequently, allow resume
3. **Human participants**: Track which human is which for multi-human tournaments
4. **Concurrent matches**: Should only run one match at a time in tournament

## Testing Strategy

1. **Unit tests**: Bracket generation algorithms
2. **Integration tests**: Tournament flow from creation to completion
3. **Manual testing**: Various participant counts and formats

## MVP Scope Summary

**Feature**: Single elimination tournament bracket

**Files to Create**:
- `rlbot_gui/tournament/__init__.py`
- `rlbot_gui/tournament/tournament_runner.py`
- `rlbot_gui/tournament/bracket_generator.py`
- `rlbot_gui/tournament/tournament_state.py`
- `rlbot_gui/gui/js/tournament-vue.js`

**Files to Modify**:
- `rlbot_gui/gui/js/main.js` - Add tournament route
- `rlbot_gui/gui/main.html` - Update keep-alive if needed
- `rlbot_gui/gui/js/main-vue.js` - Add Tournament button to navbar

**Key Integration Points**:
- Reuse `bot-pool-vue.js` for participant selection
- Reuse `eel.start_match()` for match execution
- Reuse `QSettings` pattern from story mode for persistence
- Reuse packet translation for determining winners

**Estimated Effort**: Moderate - approximately 3-5 days for a developer familiar with the codebase

**Risks**:
- Bracket visualization complexity may be underestimated
- Edge cases with odd participant counts
- State persistence and recovery from crashes

## Recommended Implementation Order

1. **Phase 1: MVP (Single Elimination)**
   - Basic tournament creation
   - Single elimination bracket generation
   - Add participants from pool
   - Start matches, record winners
   - Advance to next round
   - Declare tournament winner
   - Auto-save on match result

2. **Phase 2: Enhanced Features**
   - Round robin format
   - Double elimination format
   - Better bracket visualization
   - Export/import tournament

3. **Phase 3: Polish**
   - Tournament templates
   - Statistics tracking
   - Shareable tournament files

## Design Decisions (Confirmed)

1. **MVP Scope**: Single elimination only
2. **Draw handling**: Rocket League overtime handles draws naturally; no special handling needed unless server error occurs
3. **Human participants**: Single slot at a time (sequential play)
4. **Save behavior**: Auto-save on every match result
5. **Bracket visualization**: Custom simple implementation first

## Next Steps

1. Begin implementation with Phase 1 (single elimination)
2. Add round robin and double elimination in future iterations

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

### Bug Fixes
1. **Premature Tournament Completion**: Fixed `is_tournament_final_match()` to check `next_match_id is None` instead of counting active matches
2. **Incorrect Bye Handling**: Fixed `advance_winner()` to only auto-complete byes in round 1, not in later rounds
3. **Score Ordering**: Fixed score recording to preserve team order (team 0 = participant1, team 1 = participant2) instead of sorting by winner
4. **Frontend State Refresh**: Changed polling to fetch fresh state from backend on each iteration instead of using stale references
5. **Infinite Alert Loop**: Removed alert on tournament completion since the winner is already displayed in the header

### Technical Improvements
1. **Automatic Match Launching**: Matches now launch automatically when clicking on a bracket match (similar to story mode)
2. **Automatic Winner Detection**: The backend automatically detects match results and records winners based on team scores
3. **Improved Polling**: Frontend polls for match completion and updates the UI automatically
