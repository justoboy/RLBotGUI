# Phase 4 Tournament Bug Fixes and Human Player Redesign

## Overview

This plan addresses four critical issues before completing Phase 4 of the tournament implementation:

1. **setup_venv.bat pause issue** - The `pause` command in setup_venv.bat blocks when called from runRLBotInsideEnv.bat
2. **Match completed button** - Non-functional button leftover from previous implementation
3. **Stop match button** - Missing functionality to free up stuck matches
4. **Human player workflow redesign** - Current staging approach doesn't work with Rocket Plugin's LAN hosting

---

## Issue 1: setup_venv.bat Pause in runRLBotInsideEnv.bat

### Problem
The `setup_venv.bat` script uses `pause` commands which cause a "press enter to continue" prompt. When run from `runRLBotInsideEnv.bat`, this blocks execution and requires manual intervention.

### Solution
Modify `runRLBotInsideEnv.bat` to:
1. Check if venv exists before calling setup
2. If venv exists, skip setup and run the GUI directly
3. If venv doesn't exist or setup fails, suggest running setup_venv.bat manually

### Files Affected
- [`runRLBotInsideEnv.bat`](runRLBotInsideEnv.bat)

### Implementation Steps
1. Add venv existence check before calling setup_venv.bat
2. If venv exists, proceed directly to running the GUI
3. If venv doesn't exist, call setup_venv.bat with error handling
4. On failure, display suggestion to run setup_venv.bat manually

### Code Changes

```batch
@echo off
REM RLBotGUI Launcher
REM This script sets up the Python 3.11 virtual environment and runs RLBotGUI

set "VENV_DIR=%~dp0venv\Scripts\python.exe"

REM Check if venv exists
if exist "%VENV_DIR%" (
    echo Virtual environment found, skipping setup...
    goto RUN_GUI
)

echo Virtual environment not found, running setup...
call "%~dp0setup_venv.bat"
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Setup failed!
    echo ========================================
    echo.
    echo Please run setup_venv.bat manually to resolve issues.
    echo Then try running this script again.
    echo.
    exit /b 1
)

:RUN_GUI
REM Now run the GUI using the venv Python
"%VENV_DIR%" "%~dp0run.py"
```

---

## Issue 2: Non-functional Match Completed Button

### Problem
The "Match Complete" button in [`active.html`](rlbot_gui/gui/tournament-templates/active.html:29) triggers `showMatchCompleteModal()` which opens a modal for manually recording results. However, the system now automatically detects winners via polling in `startMatchPolling()` (tournament-vue.js:1500-1536), making this button obsolete.

### Solution
Remove the Match Complete button since:
1. Match completion is automatically detected via polling
2. Winners are automatically recorded based on team scores
3. The modal is no longer needed for this workflow

### Files Affected
- [`rlbot_gui/gui/tournament-templates/active.html`](rlbot_gui/gui/tournament-templates/active.html:29-31)
- [`rlbot_gui/gui/js/tournament-vue.js`](rlbot_gui/gui/js/tournament-vue.js:1204-1207)

### Implementation Steps
1. Remove the Match Complete button from active.html (lines 29-31)
2. Remove the `showMatchCompleteModal()` method from tournament-vue.js
3. Optionally remove the match-result-modal if no longer used elsewhere

### Code Changes

**active.html (lines 29-31):**
```html
<!-- REMOVE THIS BLOCK -->
<b-button @click="showMatchCompleteModal" variant="success" v-if="matchInProgress">
    <b-icon icon="check-circle"></b-icon> Match Complete
</b-button>
```

**tournament-vue.js (lines 1204-1207):**
```javascript
// REMOVE THIS METHOD
showMatchCompleteModal() {
    if (!this.currentMatch) return;
    this.$bvModal.show('match-result-modal');
},
```

**Note:** The match-result-modal may still be needed if users want to manually override results. Keep it for now but remove the button that triggers it.

---

## Issue 3: Stop Match Button

### Problem
When a match fails to start or gets stuck, users must restart the entire application to free up the RLBot server for another match attempt. There's no way to abort a stuck match.

### Solution
Add a "Stop Match" button that:
1. Appears when `matchInProgress` is set
2. Calls a new backend function to shut down the SetupManager
3. Clears the `matchInProgress` state
4. Allows the user to retry the same match or start a different one

### Files Affected
- [`rlbot_gui/gui/tournament-templates/active.html`](rlbot_gui/gui/tournament-templates/active.html)
- [`rlbot_gui/gui/js/tournament-vue.js`](rlbot_gui/gui/js/tournament-vue.js)
- [`rlbot_gui/tournament/tournament_runner.py`](rlbot_gui/tournament/tournament_runner.py)
- [`rlbot_gui/match_runner/match_runner.py`](rlbot_gui/match_runner/match_runner.py)

### Implementation Steps

#### Frontend (tournament-vue.js)
1. Add `stopMatch()` method to stop the current match
2. Add `matchStopFailed()` handler for error cases
3. Clear polling interval when stopping

#### Frontend (active.html)
1. Add Stop Match button next to match progress indicator
2. Button should only appear when `matchInProgress` is set

#### Backend (match_runner.py)
1. Expose `shut_down_match()` function via eel
2. This calls the existing `shut_down()` function in match_runner.py:302-304

#### Backend (tournament_runner.py)
1. Expose `tournament_stop_match()` function via eel
2. Call the match runner's shutdown function
3. Clear the matchInProgress state
4. Return success/error status

### Code Changes

**match_runner.py (add at end of file):**
```python
@eel.expose
def shut_down_match():
    """
    Shut down the current match's SetupManager.
    Called when user clicks Stop Match button.
    """
    print("Shutting down match via eel.expose")
    shut_down()
    print("Match shutdown complete")
```

**tournament_runner.py (add after tournament_start_match):**
```python
@eel.expose
def tournament_stop_match():
    """
    Stop the currently in-progress match and free up the RLBot server.
    
    Returns:
        JSON string with status
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    try:
        from rlbot_gui.match_runner.match_runner import shut_down_match
        shut_down_match()
        
        # Clear match in progress state
        # Note: The match is not marked as completed, just stopped
        # User can retry the same match or start a different one
        return json.dumps({
            'success': True,
            'message': 'Match stopped successfully'
        })
    except Exception as e:
        print(f"Error stopping match: {e}")
        return json.dumps({
            'error': f'Failed to stop match: {str(e)}'
        })
```

**tournament-vue.js (add to methods):**
```javascript
async stopMatch() {
    if (!this.matchInProgress) return;
    
    if (!confirm('Stop the current match? This will abort the match and allow you to try again.')) {
        return;
    }
    
    try {
        const result = await eel.tournament_stop_match()();
        const response = JSON.parse(result);
        
        if (response.error) {
            alert('Error stopping match: ' + response.error);
            return;
        }
        
        // Clear match in progress state
        this.matchInProgress = null;
        this.currentMatch = null;
        
        console.log('Match stopped successfully');
    } catch (error) {
        console.error('Error stopping match:', error);
        alert('Error stopping match: ' + error);
    }
},
```

**active.html (add to match control toolbar):**
```html
<!-- Add after match progress indicator -->
<b-button @click="stopMatch" variant="danger" size="md" v-if="matchInProgress">
    <b-icon icon="stop-fill"></b-icon> Stop Match
</b-button>
```

---

## Issue 4: Human Player Workflow Redesign

### Problem
The current staging workflow (opening a staging lobby with humans only, then launching the real match) doesn't work because:
1. The Rocket Plugin's LAN hosting **replaces** the RLBot server entirely
2. Starting a tournament match with `Continue and Spawn` after the host has started a LAN match works correctly
3. The staging approach breaks the connection because it triggers a new server

### New Workflow
The correct sequence for human matches is:
1. **User clicks "Open Rocket League"** - Opens RL via RLBot (no match yet)
2. **Host uses Rocket Plugin to host LAN match** - This creates the server humans will join
3. **Human players join via Rocket Plugin** - All humans connect to the LAN server
4. **User clicks "Start Match"** - RLBot injects bots into the existing server with "Continue and Spawn"

### Auto-Start Behavior Options
When auto-start is enabled and a match with humans is encountered, provide three options:

| Option | Behavior |
|--------|----------|
| **Continue (be quick)** | Auto-start continues normally; user must set up server between intervals |
| **Pause auto-start** | Auto-start pauses, giving unlimited time to set up server |
| **Skip match** | Skip this match, continue auto-starting remaining bot-only matches |

### Info Card for Human Matches
Add an info card/modal that explains:
1. How to set up human matches
2. Current tournament's mutator settings (for host to configure)
3. Max player count for the match

### Files Affected
- [`rlbot_gui/gui/tournament-templates/active.html`](rlbot_gui/gui/tournament-templates/active.html)
- [`rlbot_gui/gui/tournament-templates/modals.html`](rlbot_gui/gui/tournament-templates/modals.html)
- [`rlbot_gui/gui/js/tournament-vue.js`](rlbot_gui/gui/js/tournament-vue.js)
- [`rlbot_gui/tournament/tournament_runner.py`](rlbot_gui/tournament/tournament_runner.py)
- [`rlbot_gui/persistence/settings.py`](rlbot_gui/persistence/settings.py)

### Implementation Steps

#### 1. Add "Open Rocket League" Button

**Active.html (add to match control toolbar):**
```html
<!-- New button to open RL for human match setup -->
<b-button @click="openRocketLeague" variant="info" size="md" v-if="tournamentState && !tournamentState.completed && !matchInProgress">
    <b-icon icon="play-circle"></b-icon> Open Rocket League
</b-button>
```

**tournament-vue.js (add method):**
```javascript
async openRocketLeague() {
    try {
        // Launch RLBot which will open Rocket League
        // This uses the existing match runner but doesn't start a match
        const result = await eel.open_rocket_league()();
        const response = JSON.parse(result);
        
        if (response.error) {
            alert('Error opening Rocket League: ' + response.error);
            return;
        }
        
        console.log('Rocket League opened successfully');
    } catch (error) {
        console.error('Error opening Rocket League:', error);
        alert('Error opening Rocket League: ' + error);
    }
},
```

**tournament_runner.py (add function):**
```python
@eel.expose
def open_rocket_league() -> str:
    """
    Open Rocket League via RLBot without starting a match.
    Used for human match setup workflow.
    
    Returns:
        JSON string with status
    """
    try:
        from rlbot_gui.match_runner.match_runner import get_fresh_setup_manager
        from rlbot_gui.persistence.settings import load_settings, load_launcher_settings, launcher_preferences_from_map
        
        launcher_preference_map = load_launcher_settings()
        launcher_prefs = launcher_preferences_from_map(launcher_preference_map)
        
        sm = get_fresh_setup_manager()
        sm.connect_to_game(launcher_preference=launcher_prefs)
        
        return json.dumps({
            'success': True,
            'message': 'Rocket League opened'
        })
    except Exception as e:
        print(f"Error opening Rocket League: {e}")
        return json.dumps({
            'error': f'Failed to open Rocket League: {str(e)}'
        })
```

#### 2. Update Auto-Start Human Handling

**tournament-vue.js (update data and methods):**
```javascript
// Add to data():
autoStartHumanBehavior: 'pause',  // 'continue', 'pause', or 'skip'

// Add computed property:
autoStartHumanBehaviorLabel() {
    const labels = {
        'continue': 'Continue (be quick)',
        'pause': 'Pause auto-start',
        'skip': 'Skip match'
    };
    return labels[this.autoStartHumanBehavior] || 'Continue (be quick)';
},

// Update findNextAutoStartMatch():
findNextAutoStartMatch() {
    // Check winners bracket matches
    for (const roundMatches of this.matchesByRound) {
        for (const match of roundMatches) {
            if (match.completed) continue;
            if (!match.participant1 || !match.participant2) continue;
            
            // Check if we should skip matches with humans
            if (this.matchHasHumans(match)) {
                if (this.autoStartHumanBehavior === 'skip') {
                    continue;  // Skip this match, keep looking
                } else if (this.autoStartHumanBehavior === 'pause') {
                    return null;  // Pause auto-start
                }
                // 'continue' - proceed with this match
            }
            
            return match;
        }
    }
    
    // Check losers bracket matches (same logic)
    for (const roundMatches of this.losersBracketMatchesByRound) {
        for (const match of roundMatches) {
            if (match.completed) continue;
            if (!match.participant1 || !match.participant2) continue;
            
            if (this.matchHasHumans(match)) {
                if (this.autoStartHumanBehavior === 'skip') {
                    continue;
                } else if (this.autoStartHumanBehavior === 'pause') {
                    return null;
                }
            }
            
            return match;
        }
    }
    
    return null;
},
```

**active.html (add dropdown for human behavior):**
```html
<!-- Add to auto-start controls section -->
<b-dropdown size="sm" variant="outline-secondary" text="Human Matches" class="ml-2">
    <b-dropdown-item @click="autoStartHumanBehavior = 'continue'" :active="autoStartHumanBehavior === 'continue'">
        Continue (be quick)
    </b-dropdown-item>
    <b-dropdown-item @click="autoStartHumanBehavior = 'pause'" :active="autoStartHumanBehavior === 'pause'">
        Pause auto-start
    </b-dropdown-item>
    <b-dropdown-item @click="autoStartHumanBehavior = 'skip'" :active="autoStartHumanBehavior === 'skip'">
        Skip match
    </b-dropdown-item>
</b-dropdown>
```

#### 3. Add Human Match Info Card

**modals.html (add new modal):**
```html
<!-- Human Match Info Modal -->
<b-modal id="human-info-modal" title="Human Match Setup" centered size="lg" hide-footer>
    <div v-if="currentMatch">
        <h5>Setting Up Human Match</h5>
        
        <div class="info-card">
            <h6>Instructions:</h6>
            <ol>
                <li>Click "Open Rocket League" to launch the game</li>
                <li>Host: Press <b>Home</b> → <b>Host</b> in Rocket Plugin</li>
                <li>Ensure "Continue and Spawn" is selected in RLBot GUI Settings</li>
                <li>Human players: Press <b>Home</b> → <b>Join</b> in Rocket Plugin</li>
                <li>When all players are ready, click "Start Match"</li>
            </ol>
            
            <h6>Current Tournament Settings:</h6>
            <ul>
                <li><b>Map:</b> {{ currentMatchSettings.map || 'Default' }}</li>
                <li><b>Match Length:</b> {{ currentMatchSettings.mutators?.match_length || '5 Minutes' }}</li>
                <li><b>Max Score:</b> {{ currentMatchSettings.mutators?.max_score || '5 Goals' }}</li>
                <li><b>Game Speed:</b> {{ currentMatchSettings.mutators?.game_speed || 'Default' }}</li>
                <li><b>Boost Amount:</b> {{ currentMatchSettings.mutators?.boost_amount || 'Default' }}</li>
                <li><b>Rumble:</b> {{ currentMatchSettings.mutators?.rumble || 'None' }}</li>
                <li><b>Demolish:</b> {{ currentMatchSettings.mutators?.demolish || 'Default' }}</li>
            </ul>
            
            <h6>Player Count:</h6>
            <p>
                <b-icon icon="people"></b-icon> 
                Total players: {{ currentHumanCount }} ({{ currentTeam1Count }} vs {{ currentTeam2Count }})
            </p>
            
            <div class="alert alert-info mt-3">
                <b-icon icon="info-circle"></b-icon>
                <strong>Important:</strong> The host must configure mutators in Rocket Plugin to match
                the tournament settings above. RLBot will inject bots but cannot change match settings
                once the host has started the server.
            </div>
        </div>
        
        <div class="modal-footer mt-3">
            <b-button @click="$bvModal.hide('human-info-modal')" variant="secondary">Close</b-button>
            <b-button @click="openRocketLeague" variant="info">
                <b-icon icon="play-circle"></b-icon> Open Rocket League
            </b-button>
        </div>
    </div>
</b-modal>
```

**tournament-vue.js (add data and methods):**
```javascript
// Add to data():
currentMatchSettings: null,
currentHumanCount: 0,
currentTeam1Count: 0,
currentTeam2Count: 0,

// Add method:
showHumanInfoModal() {
    if (!this.currentMatch) return;
    
    // Get match settings
    this.currentMatchSettings = this.tournamentState?.match_settings || {};
    
    // Count humans
    this.currentHumanCount = this.matchHasHumans(this.currentMatch) ? 
        (this.currentMatch.team1?.participants?.filter(p => p.participant_type === 'human').length || 0) +
        (this.currentMatch.team2?.participants?.filter(p => p.participant_type === 'human').length || 0) : 0;
    
    this.currentTeam1Count = this.currentMatch.team1?.participants?.length || 0;
    this.currentTeam2Count = this.currentMatch.team2?.participants?.length || 0;
    
    this.$bvModal.show('human-info-modal');
},
```

**active.html (add info button):**
```html
<!-- Add to match control toolbar -->
<b-button @click="showHumanInfoModal" variant="outline-info" size="sm" v-if="tournamentState && !tournamentState.completed && !matchInProgress && hasHumanMatchInCurrentRound">
    <b-icon icon="info-circle"></b-icon> Human Match Info
</b-button>
```

#### 4. Update Staging Workflow

The existing staging workflow should be **disabled** for human matches since it doesn't work with Rocket Plugin. Instead:

1. When user clicks "Start Match" on a human match:
   - Show a warning explaining the correct workflow
   - Provide option to open info modal or proceed with "Start Match" (which will just launch RL)

**tournament_runner.py (update tournament_start_match):**
```python
# In tournament_start_match, modify the human handling:
if has_humans and use_staging:
    # Staging no longer works - just launch RL and let user know
    # The real match will be started manually after humans join
    
    # For now, just open RL without starting a match
    # TODO: Implement proper "open RL only" function
    return json.dumps({
        'success': True,
        'match_id': match_id,
        'staging': False,  # No staging, just open RL
        'has_humans': True,
        'human_count': human_count,
        'message': 'Please use Rocket Plugin to host and have humans join, then start the match with Continue and Spawn',
        'participants': [match.participant1.name, match.participant2.name]
    })
```

---

## Testing Plan

### Issue 1: setup_venv.bat
- [ ] Run runRLBotInsideEnv.bat when venv exists - should launch immediately
- [ ] Run runRLBotInsideEnv.bat when venv doesn't exist - should run setup
- [ ] Run runRLBotInsideEnv.bat when setup fails - should show error message

### Issue 2: Match Completed Button
- [ ] Verify button is removed from UI
- [ ] Verify match completion still auto-detects via polling
- [ ] Verify winner is auto-recorded

### Issue 3: Stop Match Button
- [ ] Start a match and verify stop button appears
- [ ] Click stop button and verify match terminates
- [ ] Verify match can be restarted after stopping
- [ ] Verify auto-start doesn't interfere with stopped matches

### Issue 4: Human Player Workflow
- [ ] Open Rocket League button launches game
- [ ] Auto-start "continue" behavior starts human match immediately
- [ ] Auto-start "pause" behavior waits at human match
- [ ] Auto-start "skip" behavior skips human match
- [ ] Human info modal displays correct settings
- [ ] Start match with humans shows correct workflow instructions

---

## Priority Order

1. **Issue 1** - Critical blocker for running the app
2. **Issue 2** - Quick fix, removes confusing UI element
3. **Issue 3** - Important for usability, prevents app restarts
4. **Issue 4** - Major redesign, most complex, implement last

---

## Notes

- The match-result-modal may still be useful for manual score entry in edge cases; keep it but hide the button
- Consider adding a "manual result entry" option accessible via a different path if needed
- The human workflow info should also be available from the tournament creation screen for new tournaments
- Settings persistence for auto-start human behavior should be considered for future enhancement
