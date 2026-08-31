# Tournament Feature Implementation Plan

## Overview
Add a new "Tournament" tab to RLBotGUI that allows users to create tournament brackets, add bots/humans to a pool, form teams, and run matches through a tournament structure. **Supports 1v1, 2v2, 3v3, 4v4, and 5v5 team sizes** (Rocket League has 5 kickoff spawns per side, so 5v5 is the maximum).

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
    - **Team size selection: 1v1, 2v2, 3v3, 4v4, 5v5**
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
    team_size: int  # 1, 2, 3, 4, or 5
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
| 5v5 | 2 | 4, 8, 16 | 10, 20, 40, 80 |

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
 |  [1v1] [2v2] [3v3] [4v4] [5v5]  |
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

> **Status legend:** ✅ implemented · 🚧 in progress · ⬜ not started

1. **Phase 1: MVP (Single Elimination, 1v1)** — ✅ COMPLETE
   - ✅ Basic tournament creation
   - ✅ Single elimination bracket generation
   - ✅ Add participants from pool
   - ✅ Start matches, record winners
   - ✅ Advance to next round
   - ✅ Declare tournament winner
   - ✅ Auto-save on match result
   - ✅ Import/export tournaments (implemented in Phase 1, not Phase 3 as originally planned)

2. **Phase 2: Team Size Support + Multi-Human + Formats** — ✅ COMPLETE
   - ✅ **Team formation UI and logic** (random, seeded snake draft, manual, party-mode duplicates)
   - ✅ **Support 2v2, 3v3, 4v4 team sizes**
   - ✅ **5v5 team size** (Rocket League has 5 kickoff spawns per side; max team size)
   - ✅ **Team-based bracket display** (team names + member lists per slot)
   - ✅ **Team slot assignment for matches** (reorder members within a team)
   - ✅ **Allow duplicate bots (party mode)** — same bot can fill multiple seats on a team
   - ✅ **Double elimination format** (implemented in Phase 2, not Phase 3 as originally planned)
   - ✅ **Round robin format** (implemented in Phase 2, not Phase 3 as originally planned)
   - ✅ **Multi-human support** — dynamic human count + custom usernames in the create-tournament modal
   - ✅ **Human slot assignment** — humans are participants like bots; team formation assigns them to seats; `build_match_bot_list()` maps each to the correct team/slot
   - **Note**: Both main GUI and tournament use the same `start_match_helper` / `eel.start_match` entry point ([`gui.py:62`](rlbot_gui/gui.py:62)), so no separate LAN plumbing is needed. The `bot_list` passed to `start_match_helper` correctly reflects the chosen human count, and team slot indices align with the game's expected player ordering.

 3. **Phase 3: Polish / Enhanced Features** — ✅ COMPLETE
     - ✅ **LAN Match Workflow (multi-human tournaments)** — staging→real flow with "Players Ready?" gate (see [LAN Match Workflow](#lan-match-workflow-multi-human-tournaments) below)
       - ✅ Backend: `match_has_humans()` / `count_humans_in_match()` helpers, `tournament_start_match(use_staging)`, `tournament_match_has_humans()`, `tournament_confirm_players_ready()` (launches real match with `Continue And Spawn`), `tournament_cancel_staging()`
       - ✅ `start_match_helper(..., wait_for_completion=False)` for the non-blocking staging lobby
       - ✅ Frontend: staging banner + "Players Ready — Start Match" gate, confirm/cancel, shared `startMatchPolling()` helper
     - ✅ **Better bracket visualization** — winner highlighting in match cards + CSS connector lines between rounds + emphasized final round (reference image [`rl_tournament_bracket.png`](rl_tournament_bracket.png) not present in repo; implemented a clean bracket look instead)
     - ✅ **Tournament templates** — `tournament_save_template()` / `tournament_get_templates()` / `tournament_delete_template()`; "Save as Template" button + landing-page template list with "Use" to pre-fill the create modal
     - ✅ **Statistics tracking** — `tournament_get_statistics()` (per-participant/team W-L-D, GF/GA/GD, win %, totals) + statistics panel in the active tournament view
     - ✅ **Shareable tournament files** — import/export already implemented in Phase 1 (`tournament_export_to_json` / `tournament_import_from_json` / `tournament_save_file_dialog`)
     - ✅ **Team balance indicators** — `tournament_team_balance()` now wired to a balance badge in the team panel (spread + balanced/unbalanced status)

4. **Phase 4: New Features** — 🚧 IN PROGRESS
   - See [`tournament-feature-phase4.md`](.kilo/plans/tournament-feature-phase4.md) for detailed implementation plan
   - **Priority Order:**
     1. ✅ 🐛 **Bug Fix**: Human participant validation (counting, team assignment, usernames)
     2. ✅ Random team names (100+ combinations, editable, unique within tournament)
      3. ✅ Seeding editor + manual team pairing (click-to-pair, auto-form remaining)
      4. ✅ Start match button + auto-start matches (timer, skip humans option)
      5. ✅ Swiss tournament format (log2 rounds, user-selectable tiebreakers, playoff for ties)
      6. Match history view (round-grouped, expandable stats, CSV/JSON export)
     7. Tournament mutator presets (Standard, Rumble, Hoops, etc.)

## LAN Match Workflow (Multi-Human Tournaments)

> **Context:** RLBotGUI v4 hijacks a local LAN server session. Certain actions **tear down the hosting lobby**, forcing human players to manually reconnect:
> - **Changing match settings** (game mode, mutators, map) → Rocket League closes the lobby and spins up a new local instance.
> - **The match ends** → the game tears down the temporary server session to return to a lobby state.
> - **Injecting different bots** → swapping an existing bot sometimes works on the fly, but **adding additional bot slots mid-game often crashes the local host script**, requiring a lobby rebuild.
>
> **Consequence:** If a tournament match with humans is launched directly (bots + humans together), the host has to *quickly pause the game before kickoff* to set up the LAN host and invite players. This is fragile and annoying to repeat every match.

### Recommended Flow (Phase 3)
When a match contains **one or more human participants**, do **not** launch the real match immediately. Instead:

1. **Open a "staging" match with no bots** — launch the match with only the human slots (or an empty lobby) so the game loads into the map and the host has time to:
   - Press **Home** → click **Host** inside Rocket Plugin to open the port.
   - Let each human friend **one-click Join** (their local IP stays saved in the Rocket Plugin text box — they just press Home → Join).
2. **Players-ready gate** — show a **"Players Ready?"** button in the tournament UI. The real match should only start once the operator confirms all humans are connected.
3. **Start the real match with `Existing Match Behaviour = Continue and Spawn`** — this injects the bots into the already-hosted lobby *without* tearing it down, so humans stay connected.

### Implementation Notes
- The match launch path already converges on [`start_match_helper`](rlbot_gui/match_runner/match_runner.py:184) / `eel.start_match`. The `match_settings['match_behavior']` field controls `existing_match_behavior` (see [`match_runner.py:197`](rlbot_gui/match_runner/match_runner.py:197)). For the staging→real flow, the **real** match must use `'Continue And Spawn'`.
- **Staging match**: build a `bot_list` containing only the human entries (or an empty list) and launch with `instant_start` disabled so the game idles in the map/lobby. This gives the host time to set up the LAN host.
- **Real match**: build the full `bot_list` (humans + bots) via [`build_match_bot_list()`](rlbot_gui/tournament/team_manager.py:256) and launch with `match_behavior = 'Continue And Spawn'` so bots spawn into the existing lobby.
- **UI**: Add a "Players Ready?" confirmation button in the tournament match view. When a match has humans, clicking "Start Match" should:
  1. Launch the staging match (no bots, `instant_start = False`).
  2. Show the "Players Ready?" button.
  3. On confirmation, launch the real match (`Continue And Spawn`).
- **Detection**: A match "has humans" if any participant in `team1`/`team2` (or `participant1`/`participant2` for 1v1) has `participant_type == 'human'`.
- **Fallback**: If the operator prefers the old behavior, allow a "Start immediately" option that launches the full match directly (host must pause quickly to set up LAN).
- **Warning display**: Show a warning banner in the tournament UI when a match has humans, explaining the LAN reconnection behavior and the recommended staging flow.

### Edge Cases
- **1v1 with a human**: Same staging flow applies (1 human + 1 bot).
- **All-bot matches**: No staging needed — launch directly (no humans to connect).
- **Match ends**: The lobby tears down naturally. The next match in the tournament will need the staging flow again if it has humans.
- **Bot swap mid-game**: Avoid adding bot slots mid-game (crashes the host script). Always use the staging→real flow for matches with humans.

## Design Decisions (Confirmed)

  1. **MVP Scope**: Single elimination only, starting with 1v1
  2. **Team Size Progression**: 2v2, 3v3, 4v4, and 5v5 added in Phase 2 (5v5 is the max — Rocket League has 5 kickoff spawns per side)
  3. **Draw handling**: Rocket League overtime handles draws naturally; no special handling needed unless server error occurs
  4. **Human participants**: Humans are first-class participants (like bots) with `participant_type: 'human'`. The frontend owns the human list (dynamic count + custom usernames) so operators can enter real Rocket League usernames. Team formation assigns humans to seats; `build_match_bot_list()` maps each to the correct team/slot.
  5. **Save behavior**: Auto-save on every match result
  6. **Bracket visualization**: Custom simple implementation first, showing team names/members
  7. **Team Formation**: Manual or automatic before bracket generation
  8. **Multi-Human Support**: Allow any number of humans (0-10) via the "Human Players" section in the create-tournament modal; uses same `start_match_helper` / `eel.start_match` mechanism as main GUI
  9. **Party Mode (allow_duplicates)**: When enabled, each unique participant becomes one team with all seats filled by copies of that participant — enables tournaments with fewer unique bots than seats
  10. **Dynamic Humans**: The backend `get_tournament_bots()` returns only bots; the frontend builds the human participant list dynamically (count + usernames) and merges it with selected bots before calling `tournament_new()`
  11. **LAN Match Workflow (Phase 3)**: For matches with humans, use a staging→real flow: (1) launch a no-bot staging match so the host can set up the LAN host and let humans join, (2) gate on a "Players Ready?" button, (3) launch the real match with `Existing Match Behaviour = Continue and Spawn` so bots inject into the existing lobby without tearing it down. See [LAN Match Workflow](#lan-match-workflow-multi-human-tournaments).

### Phase 4 Design Decisions (Confirmed)

  12. **Swiss Format**: log2(participants) rounds (rounded up), user-selectable tiebreaker priority (score differential, goals scored, head-to-head), head-to-head playoff match when top 2 tied
  13. **Auto-Start**: Predefined timer intervals (10s/30s/60s/120s), checkbox "skip human matches" defaults to true, manual start cancels timer
  14. **Start Match Button**: Replace click-to-start entirely, match selection highlight, Enter key shortcut, only one match selectable at a time
  15. **Random Team Names**: 100+ descriptor+noun combinations, generated during team formation, editable, re-randomize option, uniqueness enforced within tournament
  16. **Manual Team Pairing**: Click-to-pair mechanism, move participant on conflict, capacity warnings, auto-form remaining teams after manual pairing
  17. **Mutator Presets**: Single preset per tournament, quick-select game modes (Standard, Rumble, Hoops, Spike Rush, etc.), loads into dropdowns for editing
  18. **Match History**: Round-grouped with expandable stats (all packet data: goals, saves, demolitions), CSV/JSON export, auto-refresh on match completion
  19. **Seeding Editor**: Click-to-swap reordering, randomize button, accessed after mutator settings before team formation
  20. **Bye Scheduling**: Automatic fair placement for top seeds (no UI, single/double elimination only)

## Next Steps

  1. ✅ Phase 1 (1v1 single elimination) — complete
  2. ✅ Phase 2 team size support (2v2, 3v3, 4v4, 5v5) — complete
  3. ✅ Phase 2 multi-human support — complete (dynamic human count + custom usernames)
  4. ✅ Phase 2 double elimination + round robin — complete
  5. ✅ Phase 3 LAN match workflow: staging→real flow with "Players Ready?" gate for matches with humans
  6. ✅ Phase 3 polish: better bracket visualization, templates, statistics, shareable files, team balance indicator UI
  7. ⬜ **Phase 4: New Features** — See [`tournament-feature-phase4.md`](.kilo/plans/tournament-feature-phase4.md) for detailed implementation plan
      - **Priority Order:**
        1. ✅ **Bug Fix**: Human participant validation (counting, team assignment, usernames) — Fixed: `v-model.number` on count input, `v-model` on name inputs, watcher to keep `human_names` in sync with `human_count`; bracket match cards cleaned up (duplicate participant name badges removed)
        2. ✅ Random team names (100+ combinations, editable, unique within tournament)
        3. ✅ Seeding editor + manual team pairing (click-to-pair, auto-form remaining)
      4. ✅ Start match button + auto-start matches (timer, skip humans option)
      5. ✅ Swiss tournament format (log2 rounds, user-selectable tiebreakers, playoff for ties)
      6. Match history view (round-grouped, expandable stats, CSV/JSON export)
        7. Tournament mutator presets (Standard, Rumble, Hoops, etc.)

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

### Multi-Human Support (Implemented)
  Both the main GUI and tournament use the same `start_match_helper` / `eel.start_match` entry point ([`gui.py:62`](rlbot_gui/gui.py:62)), so no separate LAN plumbing is needed.

  | Aspect | Main GUI | Tournament |
  |--------|----------|------------|
  | Team Building | Dynamic drag-and-drop to blue/orange teams | Pre-formed teams from team formation phase |
  | Human Selection | Single human per team (HUMAN constant in main-vue.js) | **Dynamic count (0-10) + custom usernames** |
  | Bot List Construction | [`startMatch()`](rlbot_gui/gui/js/main-vue.js:498-514) builds `blueBots` and `orangeBots` arrays | [`build_match_bot_list()`](rlbot_gui/tournament/team_manager.py:256-295) assigns team members to slots |
  | Slot Assignment | Implicit via team array position | Explicit slot assignment (0-4 for team 0, 0-4 for team 1) |
  | Multi-Human Support | Not implemented - only supports 1 human per team | **Implemented** — any number of humans, each a first-class participant |

  **How it works**: The "Human Players" section in the create-tournament modal lets operators set a count (0-10) and enter a custom username for each human. These are built into participant objects (`participant_type: 'human'`) and merged with selected bots before calling `tournament_new()`. Team formation (random/seeded/party-mode) assigns humans to seats just like bots. `build_match_bot_list()` maps each participant to the correct team and slot, and `create_player_config()` in [`match_runner.py`](rlbot_gui/match_runner/match_runner.py:25-35) assigns each human a unique `human_index` via `IncrementingInteger` for proper input routing.

### Party Mode / Allow Duplicates (Implemented)
  When `allow_duplicates` is enabled, each unique participant becomes one team with all seats filled by copies of that participant. This enables tournaments with fewer unique bots than seats (e.g., 2 unique bots in a 5v5 tournament = 2 teams of 5 copies each). Validation only requires ≥ 2 participants instead of `team_size * 2`.

### 5v5 Team Size (Implemented)
  Rocket League has 5 kickoff spawns per side, so 5v5 is the maximum team size. `VALID_TEAM_SIZES = (1, 2, 3, 4, 5)` and `MAX_PARTICIPANTS_PER_TEAM = 5`. The `bot_list` for a 5v5 match has 10 entries (5 per team), and `create_player_config()` handles any number of players per team.

### Team Size Specific Considerations
1. **Slot Mapping**: RLBot supports up to 10 participants per match (5 per team max)
2. **Human Slot Assignment**: Humans are assigned to seats by team formation; `build_match_bot_list()` maps each to the correct team/slot; `create_player_config()` assigns unique `human_index` for input routing
3. **Team Balance**: `team_balance_report()` computes a simple strength estimate (bots=1.0, humans=0.5); UI not yet wired
4. **Bye Handling**: Byes are at team level, not participant level
5. **Minimum Teams**: All team sizes support minimum 2 teams (4-10 participants depending on size)