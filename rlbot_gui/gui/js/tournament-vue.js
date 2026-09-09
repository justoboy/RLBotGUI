import BotCard from './bot-card-vue.js'
import BotPool from './bot-pool-vue.js'
import MutatorField from './mutator-field-vue.js'
import { buildTournamentTemplate } from './tournament-templates/loader.js'


// Default mutator settings
const DEFAULT_MUTATORS = {
    match_length: '5 Minutes',
    max_score: '5 Goals',
    overtime: 'Unlimited',
    series_length: 'Unlimited',
    game_speed: 'Default',
    ball_max_speed: 'Default',
    ball_type: 'Default',
    ball_weight: 'Default',
    ball_size: 'Default',
    ball_bounciness: 'Default',
    boost_amount: 'Default',
    rumble: 'None',
    boost_strength: '1x',
    gravity: 'Default',
    demolish: 'Default',
    respawn_time: '3 Seconds'
};

// Valid values sourced from rlbot.parsing.match_settings_config_parser
const MUTATOR_OPTIONS = {
    match_length: ['5 Minutes', '10 Minutes', '20 Minutes', 'Unlimited'],
    max_score: ['Unlimited', '1 Goal', '3 Goals', '5 Goals'],
    overtime: ['Unlimited', '+5 Max, First Score', '+5 Max, Random Team'],
    series_length: ['Unlimited', '3 Games', '5 Games', '7 Games'],
    game_speed: ['Default', 'Slo-Mo', 'Time Warp'],
    ball_max_speed: ['Default', 'Slow', 'Fast', 'Super Fast'],
    ball_type: ['Default', 'Cube', 'Puck', 'Basketball'],
    ball_weight: ['Default', 'Light', 'Heavy', 'Super Light'],
    ball_size: ['Default', 'Small', 'Large', 'Gigantic'],
    ball_bounciness: ['Default', 'Low', 'High', 'Super High'],
    boost_amount: ['Default', 'Unlimited', 'Recharge (Slow)', 'Recharge (Fast)', 'No Boost'],
    rumble: ['None', 'Default', 'Slow', 'Civilized', 'Destruction Derby', 'Spring Loaded', 'Spikes Only', 'Spike Rush'],
    boost_strength: ['1x', '1.5x', '2x', '10x'],
    gravity: ['Default', 'Low', 'High', 'Super High'],
    demolish: ['Default', 'Disabled', 'Friendly Fire', 'On Contact', 'On Contact (FF)'],
    respawn_time: ['3 Seconds', '2 Seconds', '1 Second', 'Disable Goal Reset']
};

// Phase 4: Mutator presets — quick-select configurations for common game modes.
// Each preset maps to a subset of the mutator keys in DEFAULT_MUTATORS.
// Selecting a preset populates the mutator dropdowns; the user can then
// adjust individual settings. 'custom' means no preset is applied.
const MUTATOR_PRESETS = {
    'standard': {
        label: 'Standard (Soccer)',
        game_mode: 'Soccer',
        mutators: {
            match_length: '5 Minutes',
            max_score: '5 Goals',
            overtime: 'Unlimited',
            series_length: 'Unlimited',
            game_speed: 'Default',
            ball_max_speed: 'Default',
            ball_type: 'Default',
            ball_weight: 'Default',
            ball_size: 'Default',
            ball_bounciness: 'Default',
            boost_amount: 'Default',
            rumble: 'None',
            boost_strength: '1x',
            gravity: 'Default',
            demolish: 'Default',
            respawn_time: '3 Seconds'
        }
    },
    'rumble': {
        label: 'Rumble',
        game_mode: 'Rumble',
        mutators: {
            match_length: '5 Minutes',
            max_score: '5 Goals',
            overtime: 'Unlimited',
            series_length: 'Unlimited',
            game_speed: 'Default',
            ball_max_speed: 'Default',
            ball_type: 'Default',
            ball_weight: 'Default',
            ball_size: 'Default',
            ball_bounciness: 'Default',
            boost_amount: 'Default',
            rumble: 'Default',
            boost_strength: '1x',
            gravity: 'Default',
            demolish: 'Default',
            respawn_time: '3 Seconds'
        }
    },
    'hoops': {
        label: 'Hoops',
        game_mode: 'Hoops',
        mutators: {
            match_length: '5 Minutes',
            max_score: '5 Goals',
            overtime: 'Unlimited',
            series_length: 'Unlimited',
            game_speed: 'Default',
            ball_max_speed: 'Default',
            ball_type: 'Basketball',
            ball_weight: 'Default',
            ball_size: 'Default',
            ball_bounciness: 'High',
            boost_amount: 'Default',
            rumble: 'None',
            boost_strength: '1x',
            gravity: 'Default',
            demolish: 'Default',
            respawn_time: '3 Seconds'
        }
    },
    'spike_rush': {
        label: 'Spike Rush',
        game_mode: 'Soccer',
        mutators: {
            match_length: '5 Minutes',
            max_score: '5 Goals',
            overtime: 'Unlimited',
            series_length: 'Unlimited',
            game_speed: 'Default',
            ball_max_speed: 'Default',
            ball_type: 'Default',
            ball_weight: 'Default',
            ball_size: 'Default',
            ball_bounciness: 'Default',
            boost_amount: 'Default',
            rumble: 'Spike Rush',
            boost_strength: '1x',
            gravity: 'Default',
            demolish: 'Default',
            respawn_time: '3 Seconds'
        }
    },
    'boomer': {
        label: 'Boomer (Big Ball)',
        game_mode: 'Soccer',
        mutators: {
            match_length: '5 Minutes',
            max_score: '5 Goals',
            overtime: 'Unlimited',
            series_length: 'Unlimited',
            game_speed: 'Default',
            ball_max_speed: 'Default',
            ball_type: 'Default',
            ball_weight: 'Default',
            ball_size: 'Gigantic',
            ball_bounciness: 'Default',
            boost_amount: 'Default',
            rumble: 'None',
            boost_strength: '1x',
            gravity: 'Default',
            demolish: 'Default',
            respawn_time: '3 Seconds'
        }
    },
    'drop_shot': {
        label: 'Drop Shot',
        game_mode: 'Dropshot',
        mutators: {
            match_length: '5 Minutes',
            max_score: '5 Goals',
            overtime: 'Unlimited',
            series_length: 'Unlimited',
            game_speed: 'Default',
            ball_max_speed: 'Default',
            ball_type: 'Default',
            ball_weight: 'Default',
            ball_size: 'Default',
            ball_bounciness: 'Default',
            boost_amount: 'Default',
            rumble: 'None',
            boost_strength: '1x',
            gravity: 'Low',
            demolish: 'Default',
            respawn_time: '3 Seconds'
        }
    },
    'snow_day': {
        label: 'Snow Day (Low Gravity)',
        game_mode: 'Soccer',
        mutators: {
            match_length: '5 Minutes',
            max_score: '5 Goals',
            overtime: 'Unlimited',
            series_length: 'Unlimited',
            game_speed: 'Default',
            ball_max_speed: 'Default',
            ball_type: 'Default',
            ball_weight: 'Default',
            ball_size: 'Default',
            ball_bounciness: 'Low',
            boost_amount: 'Default',
            rumble: 'None',
            boost_strength: '1x',
            gravity: 'Low',
            demolish: 'Default',
            respawn_time: '3 Seconds'
        }
    },
    'hockey': {
        label: 'Hockey (Puck)',
        game_mode: 'Hockey',
        mutators: {
            match_length: '5 Minutes',
            max_score: '5 Goals',
            overtime: 'Unlimited',
            series_length: 'Unlimited',
            game_speed: 'Default',
            ball_max_speed: 'Default',
            ball_type: 'Puck',
            ball_weight: 'Default',
            ball_size: 'Default',
            ball_bounciness: 'Low',
            boost_amount: 'Default',
            rumble: 'None',
            boost_strength: '1x',
            gravity: 'Default',
            demolish: 'Default',
            respawn_time: '3 Seconds'
        }
    }
};

export default {
    name: 'tournament',
    template: buildTournamentTemplate(),
    components: {
        'bot-card': BotCard,
        'bot-pool': BotPool,
        'mutator-field': MutatorField,
    },
    data() {
        return {
            tournamentState: null,
            botPool: [],
            selectedParticipants: [],
            newTournament: {
                name: '',
                format: 'single_elimination',
                team_size: 1,
                allow_duplicates: false,
                human_count: 0,
                human_names: [],
                mutators: { ...DEFAULT_MUTATORS },
                map: '',  // Phase 4: Selected map ID (empty = default/random)
                game_mode: 'Soccer',  // Phase 4: Game mode for all matches
                // Phase 4: Swiss format settings
                swiss_rounds: 0,  // 0 = auto-calculate as ceil(log2(participants))
                swiss_tiebreakers: ['score_differential', 'goals_scored', 'head_to_head']
            },
            currentMatch: null,
            matchInProgress: null,
            savedTournaments: [],
            isSaving: false,
            MUTATOR_OPTIONS: MUTATOR_OPTIONS,
            MUTATOR_PRESETS: MUTATOR_PRESETS,
            // Phase 3: LAN Match Workflow (staging -> Players Ready -> real match)
            stagingMatchId: null,       // match_id currently in the staging phase
            stagingHumanCount: 0,       // number of humans in the staging match
            showCreateModalDialog: false, // v-model fallback for create tournament modal
            // Phase 3: Team balance indicator
            teamBalance: null,          // {balanced, spread, strengths}
            // Phase 3: Tournament templates
            templates: [],
            templateName: '',
            // Phase 3: Statistics
            statsData: null,
            // Phase 4: Random team names
            editingTeamName: -1,    // Index of team being edited, -1 if none
            _handlingEnter: false,  // Internal flag to prevent double-save on Enter
            // Phase 4: Seeding Editor
            seedingOrder: [],           // Current seeding order of participants
            selectedSeedingSwap: -1,    // Index of selected participant for swap
            // Phase 4: Manual Team Pairing
            manualPairings: [],         // List of {participant_id1, participant_id2} objects
            selectedPairingParticipants: [],  // IDs of currently selected participants
            pairingWarnings: [],        // Warnings about pairing conflicts
            // Phase 4: Start Match Button + Auto-Start
            selectedMatchId: null,      // ID of currently selected match for starting
            autoStartEnabled: false,    // Auto-start toggle
            autoStartInterval: 30,      // Auto-start interval in seconds (default 30s)
            autoStartSkipHumans: true,  // Skip matches with humans
            autoStartHumanBehavior: 'pause',  // 'continue', 'pause', or 'skip' for human matches
            autoStartTimer: null,       // Timer interval reference
            autoStartCountdown: null,   // Current countdown value
            // Phase 4: Human Match Info Modal
            currentMatchSettings: null,   // Current match settings for info modal
            currentHumanCount: 0,         // Current human count for info modal
            currentTeam1Count: 0,         // Team 1 player count for info modal
            currentTeam2Count: 0,         // Team 2 player count for info modal
            // Phase 4: Swiss format
            swissStandings: null,       // Live standings from eel.tournament_get_swiss_standings()
            // Phase 4: Tournament map selection
            mapOptions: [],             // List of available map IDs from eel.get_match_options()
            // Phase 4: Game mode options (from eel.get_match_options())
            gameModeOptions: ['Soccer', 'Hoops', 'Dropshot', 'Hockey', 'Rumble', 'Heatseeker', 'Gridiron'],
            // Phase 4: Mutator presets
            selectedPreset: 'custom',   // Currently selected mutator preset key
            // Phase 4: Match history view
            matchHistory: null,         // Match history data from eel.tournament_get_match_history()
            expandedHistoryMatches: {}, // { match_id: true } for expanded stats
            expandedHistoryRounds: {},  // { round_num: true } for expanded rounds
            activeHistoryTab: 'bracket' // 'bracket' | 'history'
        };
    },
    computed: {
        formatLabel() {
            if (!this.tournamentState) return '';
            const labels = {
                'single_elimination': 'Single Elimination',
                'double_elimination': 'Double Elimination',
                'round_robin': 'Round Robin',
                'swiss': 'Swiss'
            };
            return labels[this.tournamentState.format] || this.tournamentState.format;
        },
        // Dynamic human participants built from human_count / human_names config.
        humanParticipants() {
            const count = Math.max(0, Math.min(this.newTournament.human_count || 0, 10));
            const list = [];
            for (let i = 0; i < count; i++) {
                const name = (this.newTournament.human_names && this.newTournament.human_names[i]) || '';
                list.push({
                    name: name.trim() || `Human ${i + 1}`,
                    participant_id: `human_dynamic_${i}`,
                    participant_type: 'human',
                    type: 'human'
                });
            }
            return list;
        },
        // Total participants = selected bots + dynamic humans.
        totalParticipants() {
            return this.selectedParticipants.length + this.humanParticipants.length;
        },
        canCreateTournament() {
            const teamSize = Number(this.newTournament.team_size) || 1;
            const count = this.totalParticipants;
            if (teamSize > 1 && this.newTournament.allow_duplicates) {
                return count >= 2;
            }
            if (count < (teamSize > 1 ? teamSize * 2 : 2)) return false;
            if (teamSize > 1 && count % teamSize !== 0) return false;
            // Swiss requires an even number of entities (participants or teams)
            if (this.newTournament.format === 'swiss') {
                const entities = teamSize > 1 ? Math.floor(count / teamSize) : count;
                if (entities < 2 || entities % 2 !== 0) return false;
            }
            return true;
        },
        createBlockReason() {
            const teamSize = Number(this.newTournament.team_size) || 1;
            const count = this.totalParticipants;
            if (teamSize > 1 && this.newTournament.allow_duplicates) {
                if (count < 2) {
                    return 'Select at least 2 participants (one per team) for party mode';
                }
                return '';
            }
            if (count < (teamSize > 1 ? teamSize * 2 : 2)) {
                return `Select at least ${teamSize > 1 ? teamSize * 2 : 2} participants` +
                    (teamSize > 1 ? ` (${teamSize} per team x 2 teams)` : '');
            }
            if (teamSize > 1 && count % teamSize !== 0) {
                const missing = teamSize - (count % teamSize);
                return `Participant count (${count}) is not divisible by team size (${teamSize}). Add ${missing} more to form full teams.`;
            }
            if (this.newTournament.format === 'swiss') {
                const entities = teamSize > 1 ? Math.floor(count / teamSize) : count;
                if (entities < 2) {
                    return 'Swiss format requires at least 2 participants (or 2 teams)';
                }
                if (entities % 2 !== 0) {
                    return `Swiss format requires an even number of ${teamSize > 1 ? 'teams' : 'participants'} (got ${entities}). Add one more to make it even.`;
                }
            }
            return '';
        },
        matchesByRound() {
            if (!this.tournamentState) return [];
  
            const rounds = {};
            for (const match of this.tournamentState.matches) {
                if (!rounds[match.round_num]) {
                    rounds[match.round_num] = [];
                }
                rounds[match.round_num].push(match);
            }
  
            // Sort by round number so iteration order is deterministic
            // (important for Swiss, where rounds are generated incrementally).
            return Object.keys(rounds)
                .map(Number)
                .sort((a, b) => a - b)
                .map(rn => rounds[rn]);
        },
        currentRound() {
            if (!this.tournamentState || !this.tournamentState.matches) return 1;
            
            // Find the first round that has at least one incomplete match
            // or if all matches in a round are complete, move to next round
            const matchesByRoundNum = {};
            for (const match of this.tournamentState.matches) {
                if (!matchesByRoundNum[match.round_num]) {
                    matchesByRoundNum[match.round_num] = [];
                }
                matchesByRoundNum[match.round_num].push(match);
            }
            
            // Sort round numbers
            const roundNumbers = Object.keys(matchesByRoundNum).map(Number).sort((a, b) => a - b);
            
            // Find the first round with incomplete matches
            for (const roundNum of roundNumbers) {
                const roundMatches = matchesByRoundNum[roundNum];
                const hasIncomplete = roundMatches.some(m => !m.completed);
                if (hasIncomplete) {
                    return roundNum;
                }
            }
            
            // All rounds complete - return the last round
            return roundNumbers.length > 0 ? roundNumbers[roundNumbers.length - 1] : 1;
        },
        losersBracketMatches() {
            if (!this.tournamentState) return [];
            
            // Get the base LB matches
            const lbMatches = this.tournamentState.losers_bracket_matches || [];
            
            // For double elimination, also include the Grand Final (L-prefixed match in matches array)
            if (this.tournamentState.format === 'double_elimination') {
                const grandFinal = this.tournamentState.matches.find(m => m.match_id.startsWith('L'));
                if (grandFinal) {
                    return [...lbMatches, grandFinal];
                }
            }
            
            return lbMatches;
        },
        losersBracketMatchesByRound() {
            if (!this.losersBracketMatches || this.losersBracketMatches.length === 0) return [];
            
            const rounds = {};
            for (const match of this.losersBracketMatches) {
                if (!rounds[match.round_num]) {
                    rounds[match.round_num] = [];
                }
                rounds[match.round_num].push(match);
            }
            
            // Sort rounds by round_num and return as array
            const sortedRoundNums = Object.keys(rounds).map(Number).sort((a, b) => a - b);
            return sortedRoundNums.map(rn => ({ roundNum: rn, matches: rounds[rn] }));
        },
        // Butterfly layout: split each round into a left wing and a right wing,
        // with the final round (1 match) in the center.
        // Left wing: rounds 1..n-1 in ascending order (outer â†’ inner).
        // Right wing: rounds n-1..1 in descending order (inner â†’ outer).
        butterflyRounds() {
            if (!this.tournamentState || !this.tournamentState.matches) {
                return { left: [], center: null, right: [] };
            }
            
            // For double elimination, only include Winners Bracket matches (W-prefixed)
            // Losers Bracket matches (L-prefixed) are displayed separately
            const isDoubleElim = this.tournamentState.format === 'double_elimination';
            const matchesToInclude = isDoubleElim 
                ? this.tournamentState.matches.filter(m => m.match_id.startsWith('W'))
                : this.tournamentState.matches;
            
            const rounds = {};
            for (const match of matchesToInclude) {
                if (!rounds[match.round_num]) rounds[match.round_num] = [];
                rounds[match.round_num].push(match);
            }
            const roundNums = Object.keys(rounds).map(Number).sort((a, b) => a - b);
            
            const left = [];
            const right = [];
            let center = null;
            
            for (const rn of roundNums) {
                const matches = rounds[rn];
                if (matches.length === 1) {
                    // Final round goes in the center
                    center = { roundNum: rn, matches, isCenter: true };
                } else {
                    // Split into left and right wings
                    const half = Math.ceil(matches.length / 2);
                    left.push({ roundNum: rn, matches: matches.slice(0, half) });
                    right.push({ roundNum: rn, matches: matches.slice(half) });
                }
            }
            
            // Right wing is displayed in reverse order (finals â†’ round 1)
            right.reverse();
            
            return { left, center, right };
        },
        // Butterfly bracket positions: returns { match_id: topPercent } for each match.
        // Each wing independently spreads its round 1 matches across 0-100% of its
        // own column; later rounds are placed at the midpoint of their feeders.
        // This ensures both wings' semi-finals align at 50% with the finals.
        wbMatchPositions() {
            if (!this.tournamentState || !this.tournamentState.matches) return {};
            const { left, center, right } = this.butterflyRounds;
            const positions = {};
            const allMatches = this.tournamentState.matches;

            // Position a single wing's matches independently across 0-100%
            const positionWing = (wingRounds) => {
                if (!wingRounds || wingRounds.length === 0) return;

                // Find the round with the most matches (that's round 1)
                let r1 = wingRounds[0];
                for (const r of wingRounds) {
                    if (r.matches.length > r1.matches.length) r1 = r;
                }

                // Spread round 1 matches evenly across 0-100% with margins
                const n = r1.matches.length;
                const spacing = 100 / (n + 1);
                for (let i = 0; i < n; i++) {
                    positions[r1.matches[i].match_id] = spacing * (i + 1);
                }

                // Process remaining rounds in ascending round order
                const sorted = [...wingRounds].sort((a, b) => a.roundNum - b.roundNum);
                for (const round of sorted) {
                    if (round.roundNum === r1.roundNum) continue; // Already positioned
                    for (const match of round.matches) {
                        if (positions[match.match_id] !== undefined) continue;
                        // Find feeders (matches that feed into this match)
                        const feeders = allMatches.filter(f => f.next_match_id === match.match_id);
                        if (feeders.length > 0) {
                            const sum = feeders.reduce((acc, f) => {
                                const pos = positions[f.match_id];
                                return acc + (pos !== undefined ? pos : 50);
                            }, 0);
                            positions[match.match_id] = sum / feeders.length;
                        } else {
                            positions[match.match_id] = 50;
                        }
                    }
                }
            };

            positionWing(left);
            positionWing(right);

            // Center (finals) at 50%
            if (center) {
                for (const m of center.matches) {
                    positions[m.match_id] = 50;
                }
            }

            return positions;
        },
        lbMatchPositions() {
            if (!this.tournamentState || !this.losersBracketMatches) return {};
            return this.computeLosersBracketPositions;
        },
        
        // Compute vertical positions for Losers Bracket matches.
        // Unlike the standard computeBracketPositions, this method handles the case where
        // a later LB round has MORE matches than its feeder (due to WB losers entering).
        // Strategy:
        // 1. Position Round 1 evenly across 0-100%
        // 2. For each subsequent round:
        //    - First, position matches that have feeders (at midpoint of feeders)
        //    - Then, for remaining "entry point" matches (no LB feeders), distribute them
        //      evenly across the available space, biased toward their WB feeder positions
        computeLosersBracketPositions() {
            const matches = Array.isArray(this.losersBracketMatches) ? this.losersBracketMatches : [];
            const positions = {};
            if (!matches || matches.length === 0) return positions;

            const byId = {};
            for (const m of matches) byId[m.match_id] = m;

            // Group by round number, sorted ascending.
            const roundNums = [...new Set(matches.map(m => m.round_num))].sort((a, b) => a - b);
            const byRound = {};
            for (const rn of roundNums) {
                byRound[rn] = matches.filter(m => m.round_num === rn);
            }

            // Round 1: spread evenly across the full height.
            const first = byRound[roundNums[0]];
            const n = first.length;
            for (let i = 0; i < n; i++) {
                positions[first[i].match_id] = ((i + 0.5) / n) * 100;
            }

            // For each subsequent round, process matches in two passes:
            // Pass 1: Matches that have LB feeders (position at midpoint of feeders)
            // Pass 2: Entry point matches (no LB feeders - distribute evenly with WB bias)
            for (let r = 1; r < roundNums.length; r++) {
                const roundMatches = byRound[roundNums[r]];
                
                // Separate matches into two groups
                const withFeeders = [];
                const entryPoints = [];
                
                for (const m of roundMatches) {
                    if (positions[m.match_id] !== undefined) continue;
                    
                    // Check for LB feeders (losers_bracket_matches that point here)
                    const lbFeeders = matches.filter(f =>
                        f.next_match_id === m.match_id &&
                        byRound[f.round_num] &&
                        byRound[f.round_num].includes(m) === false // Ensure it's from a previous round
                    );
                    
                    if (lbFeeders.length > 0) {
                        withFeeders.push({ match: m, feeders: lbFeeders });
                    } else {
                        entryPoints.push(m);
                    }
                }
                
                // Pass 1: Position matches with feeders at midpoint of their feeders
                for (const {match, feeders} of withFeeders) {
                    const sum = feeders.reduce((acc, f) => {
                        const pos = positions[f.match_id];
                        return acc + (pos !== undefined ? pos : 50);
                    }, 0);
                    positions[match.match_id] = sum / feeders.length;
                }
                
                // Pass 2: For entry point matches, try to use WB feeder positions if available
                // If no WB feeders, distribute evenly across the round's space
                const entryPointCount = entryPoints.length;
                
                // First, check if there's a "shadow" from the previous LB round
                // (i.e., the number of matches in the previous round)
                const prevRoundMatches = r > 0 ? byRound[roundNums[r - 1]] : [];
                const prevRoundMaxPos = prevRoundMatches.length > 0
                    ? Math.max(...prevRoundMatches.map(m => positions[m.match_id] || 50))
                    : 100;
                const prevRoundMinPos = prevRoundMatches.length > 0
                    ? Math.min(...prevRoundMatches.map(m => positions[m.match_id] || 50))
                    : 0;
                
                // For each entry point, check if it has a WB feeder (loser_next_match_id)
                const entryPointsWithWbFeeder = [];
                const entryPointsWithoutWbFeeder = [];
                
                for (const ep of entryPoints) {
                    const wbFeeders = this.tournamentState?.matches?.filter(
                        f => f.loser_next_match_id === ep.match_id
                    ) || [];
                    
                    if (wbFeeders.length > 0 && wbFeeders.some(f => positions[f.match_id] !== undefined)) {
                        // Calculate midpoint of WB feeders
                        const sum = wbFeeders.reduce((acc, f) => {
                            const pos = positions[f.match_id];
                            return acc + (pos !== undefined ? pos : 50);
                        }, 0);
                        const avgPos = sum / wbFeeders.filter(f => positions[f.match_id] !== undefined).length;
                        entryPointsWithWbFeeder.push({ match: ep, pos: avgPos });
                    } else {
                        entryPointsWithoutWbFeeder.push(ep);
                    }
                }
                
                // Position entry points with WB feeders at their weighted position
                for (const {match, pos} of entryPointsWithWbFeeder) {
                    positions[match.match_id] = pos;
                }
                
                // Position entry points without WB feeders using gap-based distribution.
                // Each entry point is placed at the midpoint of the largest available gap
                // among already-positioned matches in this round.
                if (entryPointsWithoutWbFeeder.length > 0) {
                    const positioned = roundMatches
                        .filter(m => positions[m.match_id] !== undefined)
                        .map(m => positions[m.match_id])
                        .sort((a, b) => a - b);

                    for (const ep of entryPointsWithoutWbFeeder) {
                        // Find the largest gap between positioned matches (and edges).
                        // bestSize starts at -1 so the first real gap always wins
                        // (starting at 100 would make no real gap ever replace the default).
                        let bestGapStart = 0, bestGapEnd = 100, bestSize = -1;
                        let prev = 0;
                        for (const pos of positioned) {
                            const size = pos - prev;
                            if (size > bestSize) {
                                bestSize = size;
                                bestGapStart = prev;
                                bestGapEnd = pos;
                            }
                            prev = pos;
                        }
                        const tailSize = 100 - prev;
                        if (tailSize > bestSize) {
                            bestSize = tailSize;
                            bestGapStart = prev;
                            bestGapEnd = 100;
                        }

                        const gapMid = (bestGapStart + bestGapEnd) / 2;
                        positions[ep.match_id] = gapMid;
                        // Insert into positioned list (keep sorted for next iteration)
                        positioned.push(gapMid);
                        positioned.sort((a, b) => a - b);
                    }
                }
            }
            
            return positions;
        },
        standings() {
            if (!this.tournamentState || this.tournamentState.format !== 'round_robin') return [];

            const isTeamMode = (this.tournamentState.team_size > 1) &&
                this.tournamentState.teams && this.tournamentState.teams.length > 0;

            // Calculate standings from matches
            const standings = {};

            // Initialize standings keyed by the entity that fills the bracket slot:
            // teams (team_id) in team mode, participants (participant_id) in 1v1.
            if (isTeamMode) {
                for (const t of this.tournamentState.teams) {
                    standings[t.team_id] = {
                        participant: t,
                        played: 0,
                        wins: 0,
                        draws: 0,
                        losses: 0,
                        goals_for: 0,
                        goals_against: 0,
                        goal_difference: 0,
                        points: 0
                    };
                }
            } else {
                for (const p of this.tournamentState.participants) {
                    standings[p.participant_id] = {
                        participant: p,
                        played: 0,
                        wins: 0,
                        draws: 0,
                        losses: 0,
                        goals_for: 0,
                        goals_against: 0,
                        goal_difference: 0,
                        points: 0
                    };
                }
            }

            // Process completed matches
            for (const match of this.tournamentState.matches) {
                if (!match.completed || !match.score) continue;
                if (!match.participant1 || !match.participant2) continue;

                const p1Id = match.participant1.participant_id;
                const p2Id = match.participant2.participant_id;
                if (!standings[p1Id] || !standings[p2Id]) continue;

                const [score1, score2] = match.score;

                // Update games played
                standings[p1Id].played++;
                standings[p2Id].played++;

                // Update goals
                standings[p1Id].goals_for += score1;
                standings[p1Id].goals_against += score2;
                standings[p2Id].goals_for += score2;
                standings[p2Id].goals_against += score1;

                // Determine winner/draw
                if (score1 > score2) {
                    standings[p1Id].wins++;
                    standings[p1Id].points += 3;
                    standings[p2Id].losses++;
                } else if (score2 > score1) {
                    standings[p2Id].wins++;
                    standings[p2Id].points += 3;
                    standings[p1Id].losses++;
                } else {
                    standings[p1Id].draws++;
                    standings[p1Id].points += 1;
                    standings[p2Id].draws++;
                    standings[p2Id].points += 1;
                }
            }

            // Calculate goal difference
            for (const pId of Object.keys(standings)) {
                standings[pId].goal_difference = standings[pId].goals_for - standings[pId].goals_against;
            }

            // Convert to array and sort
            const result = Object.values(standings);
            result.sort((a, b) => {
                if (b.points !== a.points) return b.points - a.points;
                if (b.goal_difference !== a.goal_difference) return b.goal_difference - a.goal_difference;
                return b.goals_for - a.goals_for;
            });

            return result;
        },
        // Phase 4: Swiss format — group matches by round for the Swiss view.
        swissRounds() {
            if (!this.tournamentState || this.tournamentState.format !== 'swiss') return [];
            const matches = this.tournamentState.matches || [];
            const byRound = {};
            for (const m of matches) {
                if (!byRound[m.round_num]) byRound[m.round_num] = [];
                byRound[m.round_num].push(m);
            }
            const roundNums = Object.keys(byRound).map(Number).sort((a, b) => a - b);
            return roundNums.map(num => ({ num, matches: byRound[num] }));
        },
        winnerDisplayName() {
            if (!this.tournamentState) {
                return '';
            }
            // Check winner_team first (for team-based tournaments)
            if (this.tournamentState.winner_team) {
                const name = this.tournamentState.winner_team.name;
                return typeof name === 'string' ? name : '';
            }
            // Check winner (for 1v1 Swiss format)
            if (this.tournamentState.winner) {
                const name = this.tournamentState.winner.name;
                return typeof name === 'string' ? name : '';
            }
            return '';
        }
    },
    methods: {
        // ------------------------------------------------------------------
        // Butterfly bracket layout + SVG connectors
        // ------------------------------------------------------------------

        // Compute vertical positions (as % of the round column height) for a
        // list of matches. Round 1 is spread evenly across the full height;
        // every later match is placed at the midpoint of the matches that feed
        // into it (via next_match_id). This makes the bracket converge toward
        // the center, producing the classic butterfly shape.
        computeBracketPositions(matches) {
            const positions = {};
            if (!matches || matches.length === 0) return positions;

            const byId = {};
            for (const m of matches) byId[m.match_id] = m;

            // Group by round number, sorted ascending.
            const roundNums = [...new Set(matches.map(m => m.round_num))].sort((a, b) => a - b);
            const byRound = {};
            for (const rn of roundNums) {
                byRound[rn] = matches.filter(m => m.round_num === rn);
            }

            // Round 1: spread evenly across the full height.
            const first = byRound[roundNums[0]];
            const n = first.length;
            for (let i = 0; i < n; i++) {
                positions[first[i].match_id] = ((i + 0.5) / n) * 100;
            }

            // Later rounds: midpoint of feeders (matches whose next_match_id points here).
            for (let r = 1; r < roundNums.length; r++) {
                const roundMatches = byRound[roundNums[r]];
                for (const m of roundMatches) {
                    const feeders = matches.filter(f => f.next_match_id === m.match_id);
                    if (feeders.length > 0) {
                        const sum = feeders.reduce((acc, f) => acc + (positions[f.match_id] != null ? positions[f.match_id] : 50), 0);
                        positions[m.match_id] = sum / feeders.length;
                    } else {
                        // No feeder info (e.g. losers bracket entry) - center it.
                        positions[m.match_id] = 50;
                    }
                }
            }
            return positions;
        },

        // Draw SVG connector lines between rounds (butterfly bracket style).
        // Each bracket section has its own SVG overlay inside .bracket-rounds
        // (the scroll container), so the SVG scrolls naturally with the content.
        drawBracketConnectors() {
            this.$nextTick(() => {
                // Winners bracket connectors
                const wbSvg = this.$refs.wbConnectorSvg;
                const wbSection = this.$refs.wb_section;
                const wbScrollContainer = wbSection && wbSection.querySelector('.bracket-rounds');
                if (wbSvg && wbScrollContainer && this.tournamentState && this.tournamentState.matches) {
                    // Only draw connectors for Winners Bracket matches (W-prefixed).
                    // The WB Finals match has next_match_id pointing to the Grand Final
                    // (L-prefixed), which is rendered in the Losers Bracket section.
                    // Including it here would draw a stray connector across sections.
                    const wbMatches = this.tournamentState.format === 'double_elimination'
                        ? this.tournamentState.matches.filter(m => m.match_id.startsWith('W'))
                        : this.tournamentState.matches;
                    this.drawSectionConnectors(wbSvg, wbScrollContainer, wbMatches, 'rgba(0, 217, 255, 0.55)');
                }

                // Losers bracket connectors (double elimination)
                const lbSvg = this.$refs.lbConnectorSvg;
                const lbSection = this.$refs.lb_section;
                const lbScrollContainer = lbSection && lbSection.querySelector('.bracket-rounds');
                if (lbSvg && lbScrollContainer && this.tournamentState && this.tournamentState.losers_bracket_matches) {
                    this.drawSectionConnectors(lbSvg, lbScrollContainer, this.tournamentState.losers_bracket_matches, 'rgba(255, 193, 7, 0.5)');
                }
            });
        },

        // Draw elbow connectors inside a single bracket section.
        // The SVG is absolutely positioned inside the scroll container (.bracket-rounds),
        // so it scrolls naturally with the content. Coordinates are relative to
        // the scroll container's top-left corner.
        drawSectionConnectors(svg, scrollContainer, matches, stroke) {
            // Size the SVG to the scroll container's content area
            const w = Math.max(scrollContainer.scrollWidth, scrollContainer.clientWidth);
            const h = Math.max(scrollContainer.scrollHeight, scrollContainer.clientHeight);
            svg.setAttribute('width', w);
            svg.setAttribute('height', h);
            svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
            svg.style.left = '0';
            svg.style.top = '0';

            while (svg.firstChild) svg.removeChild(svg.firstChild);

            const byId = {};
            for (const m of matches) byId[m.match_id] = m;

            // Origin of the scroll container in viewport coords (accounts for scroll)
            const originX = scrollContainer.getBoundingClientRect().left;
            const originY = scrollContainer.getBoundingClientRect().top;

            for (const m of matches) {
                if (!m.next_match_id) continue;
                const target = byId[m.next_match_id];
                if (!target) continue;

                const srcEl = this.$el.querySelector(`[data-match-id="${m.match_id}"]`);
                const dstEl = this.$el.querySelector(`[data-match-id="${target.match_id}"]`);
                if (!srcEl || !dstEl) continue;

                const s = srcEl.getBoundingClientRect();
                const d = dstEl.getBoundingClientRect();

                // Determine flow direction
                const srcCenterX = s.left + s.width / 2;
                const dstCenterX = d.left + d.width / 2;
                const srcIsLeft = srcCenterX < dstCenterX;

                const gap = 4;

                // Coordinates relative to the section's top-left
                const x1 = srcIsLeft ? s.right - originX + gap : s.left - originX - gap;
                const y1 = s.top + s.height / 2 - originY;
                const x2 = srcIsLeft ? d.left - originX - gap : d.right - originX + gap;
                const y2 = d.top + d.height / 2 - originY;

                // Elbow: horizontal out, vertical to target height, horizontal in
                const midX = x1 + (x2 - x1) / 2;
                this.appendSvgLine(svg, x1, y1, midX, y1, stroke);
                this.appendSvgLine(svg, midX, y1, midX, y2, stroke);
                this.appendSvgLine(svg, midX, y2, x2, y2, stroke);
            }
        },

        // Append a single <line> element to the SVG overlay.
        appendSvgLine(svg, x1, y1, x2, y2, stroke) {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1.toFixed(1));
            line.setAttribute('y1', y1.toFixed(1));
            line.setAttribute('x2', x2.toFixed(1));
            line.setAttribute('y2', y2.toFixed(1));
            line.setAttribute('stroke', stroke);
            line.setAttribute('stroke-width', '2');
            line.setAttribute('stroke-linecap', 'round');
            svg.appendChild(line);
        },

        // Single source of truth for round naming. `bracket` is 'winners',
        // 'losers', or undefined (single elimination / swiss / round robin).
        getRoundName(roundNum, bracket) {
            if (!this.tournamentState) return `Round ${roundNum}`;
            const format = this.tournamentState.format;

            // Single elimination: name rounds by position from the END, so any
            // bracket size labels correctly (e.g. 8 players = 3 rounds:
            // Quarter-Finals, Semi-Finals, Finals).
            if (format === 'single_elimination') {
                const allRounds = (this.tournamentState.matches || []).map(m => m.round_num);
                if (allRounds.length === 0) return `Round ${roundNum}`;
                const totalRounds = Math.max(...allRounds);
                const roundsFromEnd = totalRounds - roundNum + 1;
                if (roundsFromEnd === 1) return 'Finals';
                if (roundsFromEnd === 2) return 'Semi-Finals';
                if (roundsFromEnd === 3) return 'Quarter-Finals';
                return `Round ${roundNum}`;
            }

            // Double elimination: match the bracket view naming.
            if (format === 'double_elimination') {
                if (bracket === 'losers') {
                    // Losers bracket: name by position from the end
                    const lbMatches = this.losersBracketMatches || [];
                    if (lbMatches.length === 0) return `Round ${roundNum}`;
                    const lbRounds = new Set(lbMatches.map(m => m.round_num));
                    const totalLBRounds = Math.max(...lbRounds);
                    const roundsFromEnd = totalLBRounds - roundNum + 1;
                    if (roundsFromEnd === 1) return 'Finals';
                    if (roundsFromEnd === 2) return 'Semi-Finals';
                    if (roundsFromEnd === 3) return 'Quarter-Finals';
                    return `Round ${roundNum}`;
                }
                // Winners bracket: only the last WB round gets a special name
                const wbMatches = (this.tournamentState.matches || []).filter(m => m.match_id.startsWith('W'));
                if (wbMatches.length === 0) return `Round ${roundNum}`;
                const wbRounds = new Set(wbMatches.map(m => m.round_num));
                const totalWBRounds = Math.max(...wbRounds);
                if (roundNum === totalWBRounds) return 'Semi-Finals';
                return `Round ${roundNum}`;
            }

            if (format === 'swiss') {
                const totalRounds = this.tournamentState.swiss_rounds || 0;
                return `Round ${roundNum} of ${totalRounds}`;
            }

            return `Round ${roundNum}`;
        },
        getWinnersBracketRoundName(roundNum, roundMatches) {
            return this.getRoundName(roundNum, 'winners');
        },
        getLosersBracketRoundName(roundNum, roundMatches) {
            return this.getRoundName(roundNum, 'losers');
        },
        getCurrentRoundName() {
            if (!this.tournamentState || !this.tournamentState.matches) return 'Round 1';

            // Find the first round with incomplete matches
            const matchesByRoundNum = {};
            for (const match of this.tournamentState.matches) {
                if (!matchesByRoundNum[match.round_num]) {
                    matchesByRoundNum[match.round_num] = [];
                }
                matchesByRoundNum[match.round_num].push(match);
            }

            const roundNumbers = Object.keys(matchesByRoundNum).map(Number).sort((a, b) => a - b);

            for (const roundNum of roundNumbers) {
                const hasIncomplete = matchesByRoundNum[roundNum].some(m => !m.completed);
                if (hasIncomplete) {
                    return this.getRoundName(roundNum, 'winners');
                }
            }

            // All rounds complete - show the final round name
            const lastRound = roundNumbers[roundNumbers.length - 1];
            return this.getRoundName(lastRound, 'winners');
        },
        async showCreateModal() {
            // Force a tick to ensure the modal is rendered
            await this.$nextTick();
            
            try {
                await this.loadBotPool();
            } catch (error) {
                console.error('Error loading bot pool:', error);
            }
            
            // Try both methods
            this.showCreateModalDialog = true;
            this.$nextTick(() => {
                this.$bvModal.show('create-tournament-modal');
            });
        },
        
        async loadBotPool() {
            // Load bots from the backend pool. Humans are NOT in this pool â€”
            // they are configured separately in the "Human Players" section
            // (dynamic count + custom usernames) and merged in at create time.
            if (eel.get_tournament_bots) {
                try {
                    this.botPool = await eel.get_tournament_bots()();
                } catch (err) {
                    console.error('Error calling eel.get_tournament_bots:', err);
                    this.botPool = [];
                }
            } else {
                this.botPool = [];
            }
        },
        
        toggleParticipantSelection(participant) {
            const index = this.selectedParticipants.findIndex(p => p.participant_id === participant.participant_id);
            if (index >= 0) {
                this.selectedParticipants.splice(index, 1);
            } else {
                this.selectedParticipants.push({ ...participant });
            }
        },
        
        // --- Dynamic human management ---
        setHumanCount(count) {
            const c = Math.max(0, Math.min(Number(count) || 0, 10));
            this.newTournament.human_count = c;
            // Resize the names array to match
            const names = this.newTournament.human_names || [];
            while (names.length < c) names.push('');
            this.newTournament.human_names = names.slice(0, c);
        },
        setHumanName(index, name) {
            if (!this.newTournament.human_names) this.newTournament.human_names = [];
            this.newTournament.human_names[index] = name;
        },

        async createTournament() {
            console.log('[Tournament] createTournament called');
            const teamSize = Number(this.newTournament.team_size) || 1;
            const allowDuplicates = teamSize > 1 && !!this.newTournament.allow_duplicates;
            const total = this.totalParticipants;
            console.log('[Tournament] teamSize:', teamSize, 'totalParticipants:', total);
            if (allowDuplicates) {
                if (total < 2) {
                    alert('Please select at least 2 participants (one per team) for party mode');
                    return;
                }
            } else {
                const minParticipants = teamSize > 1 ? teamSize * 2 : 2;
                if (total < minParticipants) {
                    alert(`Please select at least ${minParticipants} participants` +
                        (teamSize > 1 ? ` (${teamSize} per team x 2 teams)` : ''));
                    return;
                }
                if (teamSize > 1 && total % teamSize !== 0) {
                    const missing = teamSize - (total % teamSize);
                    alert(`Participant count (${total}) is not divisible by team size (${teamSize}). Add ${missing} more participant(s) to form full teams.`);
                    return;
                }
            }

            // Check for duplicate tournament name
            const existingTournament = this.savedTournaments.find(
                t => t.name.toLowerCase() === this.newTournament.name.toLowerCase()
            );
            if (existingTournament) {
                alert(`A tournament named "${this.newTournament.name}" already exists. Please choose a different name.`);
                return;
            }

            // Combine selected bots + dynamic humans into the full participant list
            const allParticipants = [...this.selectedParticipants, ...this.humanParticipants];
            console.log('[Tournament] Participants to create:', allParticipants.length);

            // Phase 4: Swiss format parameters
            const isSwiss = this.newTournament.format === 'swiss';
            const swissTiebreakersJson = isSwiss
                ? JSON.stringify(this.newTournament.swiss_tiebreakers || [])
                : '[]';
            const swissRounds = isSwiss ? (Number(this.newTournament.swiss_rounds) || 0) : 0;

            try {
                console.log('[Tournament] Calling eel.tournament_new...');
                const result = await eel.tournament_new(
                    this.newTournament.name,
                    this.newTournament.format,
                    JSON.stringify(allParticipants),
                    JSON.stringify(this.newTournament.mutators),
                    teamSize,
                    allowDuplicates,
                    swissTiebreakersJson,
                    swissRounds,
                    this.newTournament.map || '',
                    this.newTournament.game_mode || 'Soccer'
                )();

                console.log('[Tournament] tournament_new returned:', result.substring(0, 200));
                const state = JSON.parse(result);
                if (state.error) {
                    alert('Error creating tournament: ' + state.error);
                    return;
                }
                console.log('[Tournament] Setting tournamentState:', state.name, state.tournament_id);
                console.log('[Tournament] Before: tournamentState was', this.tournamentState ? 'set' : 'null');
                this.tournamentState = state;
                console.log('[Tournament] After: tournamentState is', this.tournamentState ? 'set' : 'null');
                this.selectedParticipants = [];
                this.newTournament = { name: '', format: 'single_elimination', team_size: 1, allow_duplicates: false, human_count: 0, human_names: [], mutators: { ...DEFAULT_MUTATORS }, map: '', game_mode: 'Soccer', swiss_rounds: 0, swiss_tiebreakers: ['score_differential', 'goals_scored', 'head_to_head'] };
                this.selectedPreset = 'custom';
                this.refreshTeamBalance();
                this.refreshStats();
                this.refreshSwissStandings();
                this.showCreateModalDialog = false;
                console.log('[Tournament] Modal closed, calling loadSavedTournaments...');
                this.loadSavedTournaments();
            } catch (error) {
                console.error('[Tournament] Error creating tournament:', error);
                alert('Error creating tournament: ' + error);
            }
        },
        
        async loadTournament() {
            try {
                const result = await eel.tournament_load()();
                if (result) {
                    this.tournamentState = JSON.parse(result);
                    this.refreshTeamBalance();
                    this.refreshStats();
                    this.refreshSwissStandings();
                }
            } catch (error) {
                console.error('Error loading tournament:', error);
            }
        },
        
        async saveTournament() {
            this.isSaving = true;
            try {
                const result = await eel.tournament_save_to_list()();
                this.tournamentState = JSON.parse(result);
                this.loadSavedTournaments();
                // Reset saving state after 2 seconds
                setTimeout(() => {
                    this.isSaving = false;
                }, 2000);
            } catch (error) {
                console.error('Error saving tournament:', error);
                alert('Error saving tournament: ' + error);
                this.isSaving = false;
            }
        },
        
        async randomizeSeeding() {
            try {
                const result = await eel.tournament_randomize_seeding()();
                this.tournamentState = JSON.parse(result);
            } catch (error) {
                console.error('Error randomizing seeding:', error);
                alert('Error randomizing seeding: ' + error);
            }
        },

        async reformTeams() {
            if (this.tournamentState.completed) {
                alert('Tournament is already complete.');
                return;
            }
            if (!confirm('Re-form teams? This will reset the bracket and all match results.')) {
                return;
            }
            try {
                const result = await eel.tournament_form_teams('random')();
                const state = JSON.parse(result);
                if (state.error) {
                    alert('Error re-forming teams: ' + state.error);
                    return;
                }
                this.tournamentState = state;
            } catch (error) {
                console.error('Error re-forming teams:', error);
                alert('Error re-forming teams: ' + error);
            }
        },

        async reorderTeamMember(teamIndex, fromSlot, toSlot) {
            if (toSlot < 0) return;
            const team = this.tournamentState.teams[teamIndex];
            if (!team || toSlot >= team.participants.length) return;
            try {
                const result = await eel.tournament_reorder_team_member(teamIndex, fromSlot, toSlot)();
                const state = JSON.parse(result);
                if (state.error) {
                    alert('Error reordering team member: ' + state.error);
                    return;
                }
                this.tournamentState = state;
            } catch (error) {
                console.error('Error reordering team member:', error);
                alert('Error reordering team member: ' + error);
            }
        },

        // Phase 4: Random team names
        startTeamNameEdit(index) {
            this.editingTeamName = index;
            this._handlingEnter = false;
            // Focus the input after DOM updates
            this.$nextTick(() => {
                const input = this.$refs.teamNameInput;
                if (input && input[index]) {
                    input[index].focus();
                    input[index].select();
                }
            });
        },

        cancelTeamNameEdit() {
            this.editingTeamName = -1;
            this._handlingEnter = false;
        },

        handleTeamNameEnter(index) {
            // Set flag to prevent blur from triggering save
            this._handlingEnter = true;
            this.saveTeamNameEdit(index);
        },

        handleTeamNameBlur(index) {
            // Only save on blur if Enter wasn't just pressed
            if (!this._handlingEnter) {
                this.saveTeamNameEdit(index);
            }
            this._handlingEnter = false;
        },

        async saveTeamNameEdit(index) {
            // First, exit edit mode to prevent re-triggering on blur
            this.editingTeamName = -1;

            const team = this.tournamentState.teams[index];
            if (!team) {
                return;
            }

            const newName = team.name.trim();
            if (!newName) {
                alert('Team name cannot be empty.');
                // Reload the state to restore the original name
                try {
                    const result = await eel.tournament_get_state()();
                    this.tournamentState = JSON.parse(result);
                } catch (e) {
                    console.error('Failed to reload state:', e);
                }
                return;
            }

            // Check for duplicate names (compare against other teams only)
            for (let i = 0; i < this.tournamentState.teams.length; i++) {
                if (i !== index) {
                    const otherName = this.tournamentState.teams[i].name;
                    if (otherName && otherName.trim().toLowerCase() === newName.toLowerCase()) {
                        alert(`Team name '${newName}' is already used by another team.`);
                        // Reload the state to restore the original name
                        try {
                            const result = await eel.tournament_get_state()();
                            this.tournamentState = JSON.parse(result);
                        } catch (e) {
                            console.error('Failed to reload state:', e);
                        }
                        return;
                    }
                }
            }

            try {
                const result = await eel.tournament_rename_team(index, newName)();
                const state = JSON.parse(result);
                if (state.error) {
                    alert('Error renaming team: ' + state.error);
                    return;
                }
                this.tournamentState = state;
            } catch (error) {
                console.error('Error renaming team:', error);
                alert('Error renaming team: ' + error);
            }
        },

        async randomizeTeamNames() {
            if (this.tournamentState.completed) {
                alert('Tournament is already complete.');
                return;
            }
            try {
                const result = await eel.tournament_randomize_team_names()();
                const state = JSON.parse(result);
                if (state.error) {
                    alert('Error randomizing team names: ' + state.error);
                    return;
                }
                this.tournamentState = state;
            } catch (error) {
                console.error('Error randomizing team names:', error);
                alert('Error randomizing team names: ' + error);
            }
        },

        participantToBot(participant) {
            return {
                name: participant.name,
                type: participant.participant_type,
                image: participant.participant_type === 'human' ? 'imgs/human.png' : 'imgs/rlbot.png',
                participant_id: participant.participant_id,
                bot_config: participant.bot_config
            };
        },
        
        isParticipantSelected(bot) {
            return this.selectedParticipants.some(p =>
                p.participant_id === bot.participant_id
            );
        },
        
        isMatchActive(match) {
            if (match.completed) return false;
            if (match.participant1 && match.participant2) return true;
            return false;
        },
        
        isMatchInProgress(match) {
            return this.matchInProgress === match.match_id;
        },
        
        showMatchResultModal(matchId) {
            // Find the match
            const match = this.findMatchById(matchId);
            if (match) {
                this.currentMatch = match;
                this.$bvModal.show('match-result-modal');
            }
        },
        
        findMatchById(matchId) {
            for (const roundMatches of this.matchesByRound) {
                for (const match of roundMatches) {
                    if (match.match_id === matchId) {
                        return match;
                    }
                }
            }
            return null;
        },
        
        // Phase 4: Start Match Button + Auto-Start
        // Select a match for starting (click-to-select, only one at a time)
        selectMatch(match) {
            if (match.completed) return;
            if (!match.participant1 || !match.participant2) return;
            
            // Toggle selection: clicking the same match deselects it
            if (this.selectedMatchId === match.match_id) {
                this.selectedMatchId = null;
            } else {
                this.selectedMatchId = match.match_id;
            }
        },
        
        // Start the selected match (called by Start Match button or Enter key)
        async startSelectedMatch() {
            // If a match is selected, start it
            if (this.selectedMatchId) {
                const match = this.findMatchById(this.selectedMatchId);
                if (!match) return;
                
                // Clear selection after starting
                this.selectedMatchId = null;
                
                // Start the match
                await this.onMatchClick(match);
                return;
            }
            
            // No match selected - find the next match to start (for auto-start)
            const nextMatch = this.findNextAutoStartMatch();
            if (nextMatch) {
                await this.onMatchClick(nextMatch);
            }
        },
        
        // Toggle auto-start mode
        toggleAutoStart() {
            if (this.autoStartEnabled) {
                // Disable auto-start
                this.autoStartEnabled = false;
                this.clearAutoStartTimer();
            } else {
                // Enable auto-start
                this.autoStartEnabled = true;
                this.startAutoStartTimer();
            }
        },
        
        // Clear the auto-start timer
        clearAutoStartTimer() {
            if (this.autoStartTimer) {
                clearInterval(this.autoStartTimer);
                this.autoStartTimer = null;
            }
            this.autoStartCountdown = null;
        },
        
        // Start the auto-start timer for the next match
        startAutoStartTimer() {
            // Clear any existing timer
            this.clearAutoStartTimer();
            
            // Find the next available match (first incomplete match in current round)
            const nextMatch = this.findNextAutoStartMatch();
            if (!nextMatch) {
                this.autoStartEnabled = false;
                return;
            }
            
            // Check if match has humans and handle based on autoStartHumanBehavior
            if (this.matchHasHumans(nextMatch)) {
                if (this.autoStartHumanBehavior === 'skip') {
                    // Find the next match without humans and start the timer for that one
                    // Temporarily set behavior to 'continue' to find a match without humans
                    const originalBehavior = this.autoStartHumanBehavior;
                    this.autoStartHumanBehavior = 'continue';
                    const nextNonHumanMatch = this.findNextAutoStartMatch();
                    this.autoStartHumanBehavior = originalBehavior;
                    
                    if (nextNonHumanMatch) {
                        this.selectedMatchId = nextNonHumanMatch.match_id;
                        this.autoStartCountdown = this.autoStartInterval;
                        
                        this.autoStartTimer = setInterval(() => {
                            this.autoStartCountdown--;
                            
                            if (this.autoStartCountdown <= 0) {
                                this.clearAutoStartTimer();
                                this.startSelectedMatch();
                            }
                        }, 1000);
                    } else {
                        // No more matches without humans, pause auto-start
                        this.autoStartEnabled = false;
                    }
                    return;
                } else if (this.autoStartHumanBehavior === 'pause') {
                    // Don't start the timer - wait for user to manually start
                    return;
                }
                // 'continue' - proceed with auto-starting this match
            }
            
            // Start countdown
            this.autoStartCountdown = this.autoStartInterval;
            
            this.autoStartTimer = setInterval(() => {
                this.autoStartCountdown--;
                
                if (this.autoStartCountdown <= 0) {
                    this.clearAutoStartTimer();
                    this.startSelectedMatch();
                }
            }, 1000);
        },
        
        // Find the next match that can be auto-started
        // For double elimination, prefer LB matches that are ready, only play WB matches
        // when LB matches are waiting for WB losers
        findNextAutoStartMatch() {
            const isDoubleElim = this.tournamentState && this.tournamentState.format === 'double_elimination';
            
            if (isDoubleElim) {
                // First, check if any LB matches are ready (have both participants)
                // This ensures we complete LB rounds as much as possible before switching to WB
                for (const roundData of this.losersBracketMatchesByRound) {
                    for (const match of roundData.matches) {
                        if (match.completed) continue;
                        if (!match.participant1 || !match.participant2) continue;
                        
                        // Check if match has humans
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
                
                // No LB matches ready, check WB matches
                for (const roundMatches of this.matchesByRound) {
                    for (const match of roundMatches) {
                        // Skip L-prefixed matches (Grand Final) - they're handled in LB section
                        if (match.match_id.startsWith('L')) continue;
                        if (match.completed) continue;
                        if (!match.participant1 || !match.participant2) continue;
                        
                        // Check if match has humans
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
            } else {
                // Check winners bracket matches (single elimination, round robin, swiss)
                for (const roundMatches of this.matchesByRound) {
                    for (const match of roundMatches) {
                        if (match.completed) continue;
                        if (!match.participant1 || !match.participant2) continue;
                        
                        // Check if match has humans
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
                
                // Check losers bracket matches (for double elimination when not using interleaved order)
                for (const roundMatches of this.losersBracketMatchesByRound) {
                    for (const match of roundMatches) {
                        if (match.completed) continue;
                        if (!match.participant1 || !match.participant2) continue;
                        
                        // Check if match has humans
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
            }
            
            return null;
        },
        
        // Get interleaved round order for double elimination
        // Returns array of { isWinnersBracket, roundNum } in execution order
        // Correct order: WB1 -> LB1 -> WB2 -> LB2 -> LB3 -> WB3 -> LB4 -> Grand Final
        // The key insight: LB3 (Quarter-Finals) determines who faces the WB Finals loser,
        // so it must run BEFORE WB Finals
        _getInterleavedRoundOrder() {
            const result = [];
            
            // Get all WB round numbers (only W-prefixed matches from matches array)
            const wbRounds = this.tournamentState.matches
                .filter(m => m.match_id.startsWith('W'))
                .map(m => m.round_num)
                .filter((v, i, a) => a.indexOf(v) === i)  // unique
                .sort((a, b) => a - b);
            
            // Get all LB round numbers from losers_bracket_matches (includes Grand Final now)
            const lbRounds = this.losersBracketMatches
                .map(m => m.round_num)
                .filter((v, i, a) => a.indexOf(v) === i)  // unique
                .sort((a, b) => a - b);
            
            // Check if Grand Final exists (L-prefixed match in matches array)
            const grandFinal = this.tournamentState.matches.find(m => m.match_id.startsWith('L'));
            
            // Find the max WB round (which is the WB Finals)
            const maxWbRound = wbRounds.length > 0 ? wbRounds[wbRounds.length - 1] : 0;
            
            // For standard double elimination with 8 players (3 WB rounds, 4 LB rounds + GF):
            // WB1 -> LB1 -> WB2 -> LB2 -> LB3 -> WB3 -> LB4 -> Grand Final
            // The pattern:
            // - After WB1: add LB1
            // - After WB2: add LB2, LB3 (LB3 runs before WB3)
            // - After WB3 (Finals): add LB4, then Grand Final
            
            let lbIndex = 0;
            
            for (let i = 0; i < wbRounds.length; i++) {
                const wbRound = wbRounds[i];
                const isLastWbRound = wbRound === maxWbRound;
                
                // Add the WB round
                result.push({ isWinnersBracket: true, roundNum: wbRound });
                
                if (isLastWbRound) {
                    // After WB Finals, add all remaining LB rounds up to (but not including) Grand Final
                    // Then add Grand Final
                    const gfRoundNum = grandFinal ? grandFinal.round_num : 999;
                    while (lbIndex < lbRounds.length && lbRounds[lbIndex] < gfRoundNum) {
                        result.push({ isWinnersBracket: false, roundNum: lbRounds[lbIndex] });
                        lbIndex++;
                    }
                    if (grandFinal) {
                        result.push({ isWinnersBracket: true, roundNum: grandFinal.round_num });
                    }
                } else {
                    // After WB Round N (not last), add LB rounds
                    // For WB1: add LB1 (1 round)
                    // For WB2: add LB2, LB3 (2 rounds)
                    // The pattern: add (wbRound) LB rounds after WB Round N
                    const lbRoundsToAdd = wbRound;
                    for (let j = 0; j < lbRoundsToAdd && lbIndex < lbRounds.length; j++) {
                        result.push({ isWinnersBracket: false, roundNum: lbRounds[lbIndex] });
                        lbIndex++;
                    }
                }
            }
            
            // Add any remaining LB rounds (shouldn't happen in standard bracket, but handle edge cases)
            while (lbIndex < lbRounds.length) {
                result.push({ isWinnersBracket: false, roundNum: lbRounds[lbIndex] });
                lbIndex++;
            }
            
            return result;
        },
        
        // Check if a match has human participants
        matchHasHumans(match) {
            if (!match || !this.tournamentState) return false;
            
            // Check team1 participants
            if (match.team1 && match.team1.participants) {
                for (const p of match.team1.participants) {
                    if (p.participant_type === 'human') return true;
                }
            }
            
            // Check team2 participants
            if (match.team2 && match.team2.participants) {
                for (const p of match.team2.participants) {
                    if (p.participant_type === 'human') return true;
                }
            }
            
            // Check participant1 (1v1 mode)
            if (match.participant1 && match.participant1.participant_type === 'human') return true;
            
            // Check participant2 (1v1 mode)
            if (match.participant2 && match.participant2.participant_type === 'human') return true;
            
            return false;
        },
        
        // Handle match completion - if auto-start is enabled, start timer for next match
        onMatchComplete() {
            if (this.autoStartEnabled) {
                // Small delay before starting the next match
                setTimeout(() => {
                    this.startAutoStartTimer();
                }, 1000);
            }
        },
        
        // Keyboard shortcut handler (Enter key starts selected match)
        handleKeyPress(event) {
            if (event.key === 'Enter' && this.selectedMatchId && !this.autoStartEnabled) {
                event.preventDefault();
                this.startSelectedMatch();
            }
        },

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
                
                // Clear polling interval if it exists
                if (this.matchPollingInterval) {
                    clearInterval(this.matchPollingInterval);
                    this.matchPollingInterval = null;
                }
                
                // Clear auto-start timer if active
                if (this.autoStartTimer) {
                    clearInterval(this.autoStartTimer);
                    this.autoStartTimer = null;
                    this.autoStartCountdown = null;
                }
            } catch (error) {
                alert('Error stopping match: ' + error);
            }
        },

        async openRocketLeague() {
            try {
                const result = await eel.open_rocket_league()();
                const response = JSON.parse(result);
                
                if (response.error) {
                    alert('Error opening Rocket League: ' + response.error);
                    return;
                }
            } catch (error) {
                alert('Error opening Rocket League: ' + error);
            }
        },

        showHumanInfoModal() {
            // Get the current tournament settings (does not require a match to be in progress)
            // Note: tournamentState.match_settings is a flat dict of mutators, not nested under 'mutators'
            const rawSettings = this.tournamentState?.match_settings || {};

            // Phase 4: The map is stored at the top level of tournamentState (not in match_settings).
            const selectedMap = this.tournamentState?.map || '';
            const mapDisplay = selectedMap ? this.formatMapName(selectedMap) : 'Default (DFH Stadium)';

            // Transform flat mutators dict to nested structure for template compatibility
            this.currentMatchSettings = {
                map: mapDisplay,
                game_mode: this.tournamentState?.game_mode || 'Soccer',
                mutators: {
                    match_length: rawSettings.match_length || '5 Minutes',
                    max_score: rawSettings.max_score || '5 Goals',
                    overtime: rawSettings.overtime || 'Unlimited',
                    series_length: rawSettings.series_length || 'Unlimited',
                    game_speed: rawSettings.game_speed || 'Default',
                    ball_max_speed: rawSettings.ball_max_speed || 'Default',
                    ball_type: rawSettings.ball_type || 'Default',
                    ball_weight: rawSettings.ball_weight || 'Default',
                    ball_size: rawSettings.ball_size || 'Default',
                    ball_bounciness: rawSettings.ball_bounciness || 'Default',
                    boost_amount: rawSettings.boost_amount || 'Default',
                    boost_strength: rawSettings.boost_strength || '1x',
                    rumble: rawSettings.rumble || 'None',
                    gravity: rawSettings.gravity || 'Default',
                    demolish: rawSettings.demolish || 'Default',
                    respawn_time: rawSettings.respawn_time || '3 Seconds'
                }
            };
            
            // Get the next match from tournament state if available (for player count info)
            let match = null;
            if (this.tournamentState) {
                const allMatches = [...(this.tournamentState.matches || []), ...(this.tournamentState.losers_bracket_matches || [])];
                match = allMatches.find(m => !m.completed && m.participant1 && m.participant2);
            }
            
            // Count players from the next available match, or use team_size to calculate expected players
            if (match) {
                // Check team-based structure (team1/team2 with participants array)
                if (match.team1?.participants && match.team2?.participants) {
                    this.currentTeam1Count = match.team1.participants.length;
                    this.currentTeam2Count = match.team2.participants.length;
                } else if (match.participant1 && match.participant2) {
                    // 1v1 structure - each participant is a single player
                    this.currentTeam1Count = 1;
                    this.currentTeam2Count = 1;
                } else {
                    // Fallback to team_size
                    const teamSize = this.tournamentState?.team_size || 1;
                    this.currentTeam1Count = teamSize;
                    this.currentTeam2Count = teamSize;
                }
                this.currentHumanCount = this.currentTeam1Count + this.currentTeam2Count;
            } else {
                // No match available - use team_size from tournament config to calculate expected players
                if (this.tournamentState) {
                    const teamSize = this.tournamentState.team_size || 1;
                    // Each match has 2 teams with team_size players each
                    this.currentHumanCount = teamSize * 2;
                    this.currentTeam1Count = teamSize;
                    this.currentTeam2Count = teamSize;
                } else {
                    this.currentHumanCount = 0;
                    this.currentTeam1Count = 0;
                    this.currentTeam2Count = 0;
                }
            }
            
            this.$bvModal.show('human-info-modal');
        },

        async onMatchClick(match) {
            if (match.completed) return;
            if (!match.participant1 || !match.participant2) return;

            // Phase 4: Clear selection when starting a match
            this.selectedMatchId = null;

            // Phase 3: LAN Match Workflow.
            // If the match has humans, ask whether to use the staging flow
            // (recommended) or start immediately (legacy behavior).
            let useStaging = false;
            if (eel.tournament_match_has_humans) {
                try {
                    const info = JSON.parse(await eel.tournament_match_has_humans(match.match_id)());
                    if (info.has_humans) {
                        const choice = confirm(
                            `This match has ${info.human_count} human player(s).\n\n` +
                            `RECOMMENDED: Open a staging lobby first so the host can set up the LAN host and let humans join, then start the real match with bots injected (no lobby teardown).\n\n` +
                            `OK = Use staging flow\nCancel = Start immediately (host must pause quickly to set up LAN)`
                        );
                        useStaging = choice;
                    }
                } catch (e) {
                    console.warn('Could not check for humans, proceeding without staging:', e);
                }
            }

            // Start the match - it will launch automatically and record the winner
            try {
                const result = await eel.tournament_start_match(match.match_id, useStaging)();
                const response = JSON.parse(result);

                if (response.error) {
                    alert(response.error);
                    return;
                }

                // Phase 3: If we launched a staging lobby, show the "Players Ready?" gate
                // and do NOT start polling for match completion yet.
                if (response.staging) {
                    this.stagingMatchId = match.match_id;
                    this.stagingHumanCount = response.human_count || 0;
                    this.currentMatch = match;
                    return;
                }

                // Match is launching - show in progress indicator
                this.matchInProgress = match.match_id;
                this.currentMatch = match;

                // Poll for tournament state update (match completion)
                this.startMatchPolling(match.match_id);
            } catch (error) {
                console.error('Error starting match:', error);
                alert('Error starting match: ' + error);
            }
        },
        
        async recordWinner(winnerName, score1, score2) {
            if (!this.currentMatch) return;
            
            try {
                const result = await eel.tournament_record_result(
                    this.currentMatch.match_id,
                    winnerName,
                    JSON.stringify([score1, score2])
                )();
                
                this.tournamentState = JSON.parse(result);
                this.currentMatch = null;
                this.matchInProgress = null;
                this.refreshTeamBalance();
                this.refreshStats();
                this.refreshSwissStandings();
                this.$bvModal.hide('match-result-modal');
                
                if (this.tournamentState.completed) {
                    console.log('Tournament Complete! Winner:', this.tournamentState.winner.name);
                }
            } catch (error) {
                console.error('Error recording result:', error);
                alert('Error recording result: ' + error);
            }
        },
        
        onParticipantDrag(participant) {
            // For manual seeding - can be enhanced later
            console.log('Dragged participant:', participant);
        },
        
        returnToHome() {
            this.$router.replace('/');
        },
        
        returnToLanding() {
            // Delete the tournament and go back to the landing page
            eel.tournament_delete();
            this.tournamentState = null;
            this.loadSavedTournaments();
        },
        
        deleteTournament() {
            // Delete the tournament and go back to the landing page
            eel.tournament_delete();
            this.tournamentState = null;
            this.loadSavedTournaments();
        },
        
        loadSavedTournaments() {
            // Load list of saved tournaments from backend
            try {
                if (eel.tournament_get_saved_list) {
                    const saved = eel.tournament_get_saved_list()();
                    saved.then(result => {
                        this.savedTournaments = JSON.parse(result);
                    });
                } else {
                    this.savedTournaments = [];
                }
            } catch (error) {
                this.savedTournaments = [];
            }
        },
        
        loadSavedTournament(tournament) {
            // Load the tournament from backend by ID
            if (eel.tournament_load_from_id) {
                eel.tournament_load_from_id(tournament.tournament_id)().then(result => {
                    const state = JSON.parse(result);
                    if (state.error) {
                        alert('Error loading tournament: ' + state.error);
                    } else {
                        this.tournamentState = state;
                        this.refreshTeamBalance();
                        this.refreshStats();
                        this.refreshSwissStandings();
                    }
                });
            } else {
                console.error('[Tournament] eel.tournament_load_from_id is not defined');
            }
        },
        
        deleteSavedTournament(tournamentId) {
            // Remove from saved tournaments list via backend
            if (eel.tournament_delete_from_list) {
                eel.tournament_delete_from_list(tournamentId)().then(() => {
                    this.loadSavedTournaments();
                });
            }
        },
        
        formatLabelFromData(format) {
            const labels = {
                'single_elimination': 'Single Elimination',
                'double_elimination': 'Double Elimination',
                'round_robin': 'Round Robin',
                'swiss': 'Swiss'
            };
            return labels[format] || format;
        },
        
        resetMutatorsToDefault() {
            this.newTournament.mutators = { ...DEFAULT_MUTATORS };
            this.selectedPreset = 'custom';
        },

        // Phase 4: When the game mode changes, sync the map and mutator preset
        // to the mode's canonical defaults (e.g. Hoops → Dunk House, Gridiron →
        // Champions Field NFL). The operator can still adjust anything afterwards.
        onGameModeChange(mode) {
            const modeDefaults = {
                'Soccer': { map: 'DFHStadium', preset: 'standard' },
                'Hoops': { map: 'Hoops_DunkHouse', preset: 'hoops' },
                'Dropshot': { map: 'DropShot_Core707', preset: 'drop_shot' },
                'Hockey': { map: 'DFHStadium', preset: 'hockey' },
                'Rumble': { map: 'DFHStadium', preset: 'rumble' },
                'Heatseeker': { map: 'DFHStadium', preset: 'standard' },
                'Gridiron': { map: 'ChampionsField_NFL', preset: 'standard' }
            };
            const def = modeDefaults[mode] || modeDefaults['Soccer'];
            this.newTournament.map = def.map;
            this.applyPreset(def.preset);
        },

        // ------------------------------------------------------------------
        // Phase 4: Tournament map selection
        // ------------------------------------------------------------------
        async loadMapOptions() {
            // Reuse the existing eel.get_match_options() which returns
            // { map_types: [...], game_modes: [...], match_behaviours: [...], mutators: {...} }.
            if (!eel.get_match_options) return;
            try {
                const options = await eel.get_match_options()();
                if (options && Array.isArray(options.map_types)) {
                    this.mapOptions = options.map_types;
                }
                if (options && Array.isArray(options.game_modes) && options.game_modes.length > 0) {
                    this.gameModeOptions = options.game_modes;
                }
            } catch (e) {
                console.error('Error loading map options:', e);
                this.mapOptions = [];
            }
        },

        // Convert a map ID (e.g. 'DFHStadium_Stormy') to a friendly name
        // (e.g. 'DFH Stadium Stormy').
        formatMapName(mapId) {
            if (!mapId) return '';
            return mapId
                .replace(/_/g, ' ')
                .replace(/([a-z])([A-Z])/g, '$1 $2');
        },

        // ------------------------------------------------------------------
        // Phase 4: Mutator presets
        // ------------------------------------------------------------------
        applyPreset(presetKey) {
            this.selectedPreset = presetKey;
            if (presetKey === 'custom' || !MUTATOR_PRESETS[presetKey]) {
                // No preset — keep current values (or reset to defaults)
                return;
            }
            const preset = MUTATOR_PRESETS[presetKey];
            this.newTournament.mutators = { ...DEFAULT_MUTATORS, ...preset.mutators };
            // NOTE: do NOT set game_mode here. The game mode is the source of truth
            // for the map/preset sync; setting it here would re-trigger the
            // game_mode watcher and clobber the map the user just selected.
        },

        // ------------------------------------------------------------------
        // Phase 4: Match history view
        // ------------------------------------------------------------------
        async refreshMatchHistory() {
            if (!this.tournamentState) {
                this.matchHistory = null;
                return;
            }
            if (!eel.tournament_get_match_history) {
                this.matchHistory = null;
                return;
            }
            try {
                const result = await eel.tournament_get_match_history()();
                const data = JSON.parse(result);
                if (data.error) {
                    this.matchHistory = null;
                    return;
                }
                // Filter out bye matches (auto-completed, never actually played)
                if (data && Array.isArray(data.rounds)) {
                    data.rounds = data.rounds
                        .map(round => ({
                            ...round,
                            matches: (round.matches || []).filter(m => !m.is_bye)
                        }))
                        .filter(round => round.matches.length > 0);
                    // Expand all rounds by default (composite key so WB and LB
                    // rounds with the same round_num don't collide)
                    for (const round of data.rounds) {
                        this.$set(this.expandedHistoryRounds, this.historyRoundKey(round), true);
                    }
                }
                this.matchHistory = data;
            } catch (e) {
                console.error('Error fetching match history:', e);
                this.matchHistory = null;
            }
        },

        switchHistoryTab(tab) {
            this.activeHistoryTab = tab;
            if (tab === 'history' && this.tournamentState) {
                this.refreshMatchHistory();
            }
        },

        // Composite key for expandedHistoryRounds so WB and LB rounds with the
        // same round_num don't collide in double elimination.
        historyRoundKey(round) {
            return `${round.bracket || 'main'}-${round.round_num}`;
        },

        toggleHistoryRound(round) {
            const key = this.historyRoundKey(round);
            this.$set(this.expandedHistoryRounds, key, !this.expandedHistoryRounds[key]);
        },

        toggleHistoryMatch(matchId) {
            if (this.expandedHistoryMatches[matchId]) {
                this.$delete(this.expandedHistoryMatches, matchId);
            } else {
                this.$set(this.expandedHistoryMatches, matchId, true);
            }
        },

        // Build a CSV string from the match history data.
        buildHistoryCSV() {
            if (!this.matchHistory || !Array.isArray(this.matchHistory.rounds)) return '';
            const headers = [
                'Round', 'Match ID', 'Team 1', 'Team 2',
                'Score 1', 'Score 2', 'Winner', 'Completed'
            ];
            const rows = [headers.join(',')];
            const esc = (v) => {
                const s = (v === null || v === undefined) ? '' : String(v);
                if (s.includes(',') || s.includes('"') || s.includes('\n')) {
                    return '"' + s.replace(/"/g, '""') + '"';
                }
                return s;
            };
            for (const round of this.matchHistory.rounds) {
                for (const m of round.matches) {
                    const row = [
                        round.round_num,
                        m.match_id,
                        m.team1_name || m.participant1_name || '',
                        m.team2_name || m.participant2_name || '',
                        m.score ? m.score[0] : '',
                        m.score ? m.score[1] : '',
                        m.winner_name || '',
                        m.completed ? 'Yes' : 'No'
                    ];
                    rows.push(row.map(esc).join(','));
                }
            }
            return rows.join('\n');
        },

        async exportHistoryCSV() {
            if (!this.matchHistory) {
                alert('No match history to export.');
                return;
            }
            const csv = this.buildHistoryCSV();
            const defaultName = `${(this.tournamentState.name || 'tournament').replace(/[^a-z0-9]/gi, '_')}_match_history.csv`;
            try {
                const result = await eel.tournament_save_file_dialog(csv, defaultName)();
                const resultData = JSON.parse(result);
                if (resultData.cancelled) return;
                if (resultData.error) {
                    alert('Error saving CSV: ' + resultData.error);
                    return;
                }
                alert('Match history exported to: ' + resultData.path);
            } catch (error) {
                console.error('Error exporting CSV:', error);
                alert('Error exporting CSV: ' + error);
            }
        },

        async exportHistoryJSON() {
            if (!this.matchHistory) {
                alert('No match history to export.');
                return;
            }
            const jsonStr = JSON.stringify(this.matchHistory, null, 2);
            const defaultName = `${(this.tournamentState.name || 'tournament').replace(/[^a-z0-9]/gi, '_')}_match_history.json`;
            try {
                const result = await eel.tournament_save_file_dialog(jsonStr, defaultName)();
                const resultData = JSON.parse(result);
                if (resultData.cancelled) return;
                if (resultData.error) {
                    alert('Error saving JSON: ' + resultData.error);
                    return;
                }
                alert('Match history exported to: ' + resultData.path);
            } catch (error) {
                console.error('Error exporting JSON:', error);
                alert('Error exporting JSON: ' + error);
            }
        },
        
        async exportTournament() {
            if (!this.tournamentState) return;
            
            try {
                const jsonStr = await eel.tournament_export_to_json()();
                const data = JSON.parse(jsonStr);
                
                if (data.error) {
                    alert('Error exporting tournament: ' + data.error);
                    return;
                }
                
                // Ask the user where to save the file via a native save dialog
                // (delegated to PyQt5 on the backend, see tournament_save_file_dialog)
                const defaultName = `${this.tournamentState.name.replace(/[^a-z0-9]/gi, '_')}_tournament.json`;
                const result = await eel.tournament_save_file_dialog(jsonStr, defaultName)();
                const resultData = JSON.parse(result);
                
                if (resultData.cancelled) {
                    // User cancelled the save dialog
                    return;
                }
                
                if (resultData.error) {
                    alert('Error saving tournament file: ' + resultData.error);
                    return;
                }
                
                alert('Tournament exported to: ' + resultData.path);
            } catch (error) {
                console.error('Error exporting tournament:', error);
                alert('Error exporting tournament: ' + error);
            }
        },
        
        triggerImportFilePicker() {
            // Reset the input so the same file can be selected again
            this.$refs.importFileInput.value = '';
            this.$refs.importFileInput.click();
        },
        
        handleImportFileSelected(event) {
            const file = event.target.files && event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (e) => {
                this.importTournament(e.target.result);
            };
            reader.onerror = () => {
                alert('Error reading file: ' + file.name);
            };
            reader.readAsText(file);
        },
        
        async importTournament(jsonStr) {
            try {
                // Validate JSON
                JSON.parse(jsonStr);
                
                const result = await eel.tournament_import_from_json(jsonStr)();
                const data = JSON.parse(result);
                
                if (data.error) {
                    alert('Error importing tournament: ' + data.error);
                    return;
                }
                
                this.tournamentState = data;
                this.refreshTeamBalance();
                this.refreshStats();
                this.refreshSwissStandings();
                alert('Tournament imported successfully!');
            } catch (error) {
                console.error('Error importing tournament:', error);
                alert('Invalid JSON format: ' + error);
            }
        },

        // ------------------------------------------------------------------
        // Phase 3: LAN Match Workflow (staging -> Players Ready -> real match)
        // ------------------------------------------------------------------
        async confirmPlayersReady() {
            if (!this.stagingMatchId) return;
            const matchId = this.stagingMatchId;
            this.stagingMatchId = null;
            try {
                const result = await eel.tournament_confirm_players_ready(matchId)();
                const response = JSON.parse(result);
                if (response.error) {
                    alert('Error starting real match: ' + response.error);
                    return;
                }
                // Real match is now launching - poll for completion.
                this.matchInProgress = matchId;
                this.startMatchPolling(matchId);
            } catch (error) {
                console.error('Error confirming players ready:', error);
                alert('Error confirming players ready: ' + error);
            }
        },

        async cancelStaging() {
            if (!this.stagingMatchId) return;
            const matchId = this.stagingMatchId;
            this.stagingMatchId = null;
            try {
                await eel.tournament_cancel_staging(matchId)();
            } catch (error) {
                console.warn('Error cancelling staging:', error);
            }
        },

        // Shared polling helper used by both the direct and staging flows.
        startMatchPolling(matchId) {
            // Clear any existing polling interval first
            if (this.matchPollingInterval) {
                clearInterval(this.matchPollingInterval);
                this.matchPollingInterval = null;
            }
            
            const pollInterval = setInterval(async () => {
                try {
                    const freshState = await eel.tournament_get_state()();
                    if (!freshState) return;
                    const currentState = JSON.parse(freshState);
                    let updatedMatch = null;
                    if (currentState.matches && Array.isArray(currentState.matches)) {
                        updatedMatch = currentState.matches.find(m => m.match_id === matchId);
                    }
                    if (!updatedMatch && currentState.losers_bracket_matches && Array.isArray(currentState.losers_bracket_matches)) {
                        updatedMatch = currentState.losers_bracket_matches.find(m => m.match_id === matchId);
                    }
                    if (updatedMatch && updatedMatch.completed) {
                        // Simplify winner objects to plain { name } to avoid Vue
                        // reactivity proxy issues with nested dataclass objects.
                        if (currentState.winner && typeof currentState.winner.name === 'string') {
                            currentState.winner = { name: currentState.winner.name };
                        }
                        if (currentState.winner_team && typeof currentState.winner_team.name === 'string') {
                            currentState.winner_team = { name: currentState.winner_team.name };
                        }
                        this.$set(this, 'tournamentState', currentState);
                        this.matchInProgress = null;
                        this.currentMatch = null;
                        clearInterval(pollInterval);
                        this.matchPollingInterval = null;
                        this.refreshTeamBalance();
                        this.refreshStats();
                        this.refreshSwissStandings();
                        // Phase 4: Refresh match history so new results appear immediately
                        this.refreshMatchHistory();
                        // Phase 4: Auto-start next match if enabled
                        this.onMatchComplete();
                    }
                } catch (e) {
                }
            }, 1000);
            this.matchPollingInterval = pollInterval;
            setTimeout(() => { clearInterval(pollInterval); this.matchPollingInterval = null; }, 300000);
        },

        // ------------------------------------------------------------------
        // Phase 3: Team balance indicator
        // ------------------------------------------------------------------
        async refreshTeamBalance() {
            if (!this.tournamentState || this.tournamentState.team_size <= 1) {
                this.teamBalance = null;
                return;
            }
            try {
                const result = await eel.tournament_team_balance()();
                const data = JSON.parse(result);
                this.teamBalance = data.error ? null : data;
            } catch (e) {
                this.teamBalance = null;
            }
        },

        // ------------------------------------------------------------------
        // Phase 3: Statistics tracking
        // ------------------------------------------------------------------
        async refreshStats() {
            if (!this.tournamentState) {
                this.statsData = null;
                return;
            }
            try {
                const result = await eel.tournament_get_statistics()();
                const data = JSON.parse(result);
                this.statsData = data.error ? null : data;
            } catch (e) {
                this.statsData = null;
            }
        },

        // ------------------------------------------------------------------
        // Phase 4: Swiss format
        // ------------------------------------------------------------------
        swissTiebreakerLabel(tb) {
            const labels = {
                'score_differential': 'Score differential (goals for - goals against)',
                'goals_scored': 'Total goals scored',
                'head_to_head': 'Head-to-head result'
            };
            return labels[tb] || tb;
        },

        moveSwissTiebreaker(from, to) {
            const list = this.newTournament.swiss_tiebreakers;
            if (to < 0 || to >= list.length) return;
            const [item] = list.splice(from, 1);
            list.splice(to, 0, item);
        },

        async refreshSwissStandings() {
            if (!this.tournamentState || this.tournamentState.format !== 'swiss') {
                this.swissStandings = null;
                return;
            }
            try {
                const result = await eel.tournament_get_swiss_standings()();
                const data = JSON.parse(result);
                this.swissStandings = data.error ? null : data;
            } catch (e) {
                console.error('Error fetching Swiss standings:', e);
                this.swissStandings = null;
            }
        },

        // ------------------------------------------------------------------
        // Phase 3: Tournament templates
        // ------------------------------------------------------------------
        loadTemplates() {
            if (eel.tournament_get_templates) {
                eel.tournament_get_templates()().then(result => {
                    this.templates = JSON.parse(result);
                });
            }
        },

        async saveAsTemplate() {
            if (!this.tournamentState) return;
            const name = prompt('Template name:', this.tournamentState.name + ' (template)');
            if (!name || !name.trim()) return;
            const config = {
                format: this.tournamentState.format,
                team_size: this.tournamentState.team_size,
                allow_duplicates: !!this.tournamentState.allow_duplicates,
                mutators: this.tournamentState.match_settings || {},
                map: this.tournamentState.map || '',
                game_mode: this.tournamentState.game_mode || 'Soccer',
                human_count: 0,
                human_names: []
            };
            try {
                const result = await eel.tournament_save_template(name.trim(), JSON.stringify(config))();
                const data = JSON.parse(result);
                if (data.error) {
                    alert('Error saving template: ' + data.error);
                    return;
                }
                this.loadTemplates();
                alert('Template saved: ' + name.trim());
            } catch (error) {
                console.error('Error saving template:', error);
                alert('Error saving template: ' + error);
            }
        },

        applyTemplate(tpl) {
            // Pre-fill the create-tournament modal from the template config.
            const cfg = tpl.config || {};
            this.newTournament.format = cfg.format || 'single_elimination';
            this.newTournament.team_size = cfg.team_size || 1;
            this.newTournament.allow_duplicates = !!cfg.allow_duplicates;
            this.newTournament.mutators = { ...DEFAULT_MUTATORS, ...(cfg.mutators || {}) };
            this.newTournament.map = cfg.map || '';
            this.newTournament.game_mode = cfg.game_mode || 'Soccer';
            this.newTournament.human_count = cfg.human_count || 0;
            this.newTournament.human_names = cfg.human_names || [];
            this.newTournament.name = '';
            this.showCreateModal();
        },

        async deleteTemplate(templateId) {
            if (!confirm('Delete this template?')) return;
            try {
                await eel.tournament_delete_template(templateId)();
                this.loadTemplates();
            } catch (error) {
                console.error('Error deleting template:', error);
            }
        },

        // ------------------------------------------------------------------
        // Phase 4: Seeding Editor
        // ------------------------------------------------------------------
        async loadSeedingOrder() {
            if (!this.tournamentState) return;
            try {
                const result = await eel.tournament_get_current_seeding()();
                this.seedingOrder = JSON.parse(result) || [];
            } catch (error) {
                console.error('Error loading seeding order:', error);
                this.seedingOrder = [];
            }
        },

        handleSeedingClick(index) {
            if (this.selectedSeedingSwap === -1) {
                // First click: select this participant
                this.selectedSeedingSwap = index;
            } else if (this.selectedSeedingSwap === index) {
                // Click same participant: deselect
                this.selectedSeedingSwap = -1;
            } else {
                // Second click: swap with selected
                this.performSeedingSwap(this.selectedSeedingSwap, index);
                this.selectedSeedingSwap = -1;
            }
        },

        async performSeedingSwap(idx1, idx2) {
            const p1 = this.seedingOrder[idx1];
            const p2 = this.seedingOrder[idx2];
            if (!p1 || !p2) return;

            try {
                const result = await eel.tournament_swap_seeds(p1.participant_id, p2.participant_id)();
                const state = JSON.parse(result);
                if (state.error) {
                    alert('Error swapping seeds: ' + state.error);
                } else {
                    this.tournamentState = state;
                    await this.loadSeedingOrder();
                }
            } catch (error) {
                console.error('Error swapping seeds:', error);
                alert('Error swapping seeds: ' + error);
            }
        },

        async randomizeSeedingFromEditor() {
            try {
                const result = await eel.tournament_randomize_seeding()();
                const state = JSON.parse(result);
                if (state.error) {
                    alert('Error randomizing seeding: ' + state.error);
                } else {
                    this.tournamentState = state;
                    await this.loadSeedingOrder();
                }
            } catch (error) {
                console.error('Error randomizing seeding:', error);
                alert('Error randomizing seeding: ' + error);
            }
        },

        openSeedingEditor() {
            this.loadSeedingOrder();
            this.selectedSeedingSwap = -1;
            this.$nextTick(() => {
                this.$bvModal.show('seeding-editor-modal');
            });
        },

        closeSeedingEditor() {
            this.$bvModal.hide('seeding-editor-modal');
        },

        // ------------------------------------------------------------------
        // Phase 4: Manual Team Pairing
        // ------------------------------------------------------------------
        openManualPairingModal() {
            this.manualPairings = [];
            this.selectedPairingParticipants = [];
            this.pairingWarnings = [];
            this.$nextTick(() => {
                this.$bvModal.show('manual-pairing-modal');
            });
        },

        closeManualPairingModal() {
            this.$bvModal.hide('manual-pairing-modal');
        },

        togglePairingSelection(participant) {
            const idx = this.selectedPairingParticipants.indexOf(participant.participant_id);
            if (idx >= 0) {
                // Deselect
                this.selectedPairingParticipants.splice(idx, 1);
            } else {
                // Select (max 2)
                if (this.selectedPairingParticipants.length < 2) {
                    this.selectedPairingParticipants.push(participant.participant_id);
                } else {
                    // Replace the first selection
                    this.selectedPairingParticipants = [participant.participant_id];
                }
            }
        },

        isParticipantAlreadyPaired(participantId) {
            return this.manualPairings.some(
                p => p.participant_id1 === participantId || p.participant_id2 === participantId
            );
        },

        getParticipantName(participantId) {
            const p = this.tournamentState?.participants?.find(p => p.participant_id === participantId);
            return p ? p.name : participantId;
        },

        addPairing() {
            if (this.selectedPairingParticipants.length !== 2) return;

            const pair = {
                participant_id1: this.selectedPairingParticipants[0],
                participant_id2: this.selectedPairingParticipants[1]
            };

            // Remove any existing pairings involving these participants
            this.manualPairings = this.manualPairings.filter(
                p => p.participant_id1 !== pair.participant_id1 &&
                     p.participant_id2 !== pair.participant_id1 &&
                     p.participant_id1 !== pair.participant_id2 &&
                     p.participant_id2 !== pair.participant_id2
            );

            // Add the new pairing
            this.manualPairings.push(pair);

            // Clear selection
            this.selectedPairingParticipants = [];

            // Update warnings
            this.updatePairingWarnings();
        },

        removePairing(index) {
            this.manualPairings.splice(index, 1);
            this.updatePairingWarnings();
        },

        clearPairings() {
            this.manualPairings = [];
            this.selectedPairingParticipants = [];
            this.pairingWarnings = [];
        },

        updatePairingWarnings() {
            this.pairingWarnings = [];

            // Check for team size conflicts
            const teamSize = this.tournamentState?.team_size || 1;

            // Count participants in each pairing group
            const groupSizes = {};
            for (const pair of this.manualPairings) {
                if (!groupSizes[pair.participant_id1]) groupSizes[pair.participant_id1] = new Set();
                if (!groupSizes[pair.participant_id2]) groupSizes[pair.participant_id2] = new Set();
                groupSizes[pair.participant_id1].add(pair.participant_id1);
                groupSizes[pair.participant_id1].add(pair.participant_id2);
                groupSizes[pair.participant_id2].add(pair.participant_id1);
                groupSizes[pair.participant_id2].add(pair.participant_id2);
            }

            // Find connected components
            const visited = new Set();
            for (const pid of Object.keys(groupSizes)) {
                if (visited.has(pid)) continue;

                const component = new Set();
                const stack = [pid];
                while (stack.length > 0) {
                    const current = stack.pop();
                    if (visited.has(current)) continue;
                    visited.add(current);
                    component.add(current);
                    for (const other of groupSizes[current] || []) {
                        if (!visited.has(other)) {
                            stack.push(other);
                        }
                    }
                }

                if (component.size > teamSize) {
                    this.pairingWarnings.push(
                        `Group of ${component.size} participants exceeds team size (${teamSize}). ` +
                        `Please reduce pairings.`
                    );
                }
            }
        },

        get canFormTeamsWithPairings() {
            return this.tournamentState?.team_size > 1 &&
                   this.tournamentState?.participants?.length > 0 &&
                   this.pairingWarnings.length === 0;
        },

        async formTeamsWithPairings() {
            if (!this.canFormTeamsWithPairings) return;

            try {
                const result = await eel.tournament_form_teams_with_pairings(
                    JSON.stringify(this.manualPairings),
                    '[]'  // No custom names for now
                )();
                const state = JSON.parse(result);
                if (state.error) {
                    alert('Error forming teams: ' + state.error);
                } else {
                    this.tournamentState = state;
                    this.$bvModal.hide('manual-pairing-modal');
                    this.refreshTeamBalance();
                }
            } catch (error) {
                console.error('Error forming teams:', error);
                alert('Error forming teams: ' + error);
            }
        }
    },
    created() {
        // Load saved tournaments list
        this.loadSavedTournaments();
        // Phase 3: Load tournament templates
        this.loadTemplates();
        // Load existing tournament if available
        this.loadTournament();
    },
    
    mounted() {
        // Draw bracket connectors after initial render
        this.$nextTick(() => {
            this.drawBracketConnectors();
        });
        // Redraw connectors when the window resizes
        this._bracketResizeHandler = () => this.drawBracketConnectors();
        window.addEventListener('resize', this._bracketResizeHandler);
        
        // Phase 4: Add keyboard event listener for Enter key shortcut
        this._keyPressHandler = (event) => this.handleKeyPress(event);
        window.addEventListener('keydown', this._keyPressHandler);

        // Phase 4: Load available maps for the map selector
        this.loadMapOptions();
    },
    beforeDestroy() {
        if (this._bracketResizeHandler) {
            window.removeEventListener('resize', this._bracketResizeHandler);
            this._bracketResizeHandler = null;
        }
        // Phase 4: Remove keyboard event listener
        if (this._keyPressHandler) {
            window.removeEventListener('keydown', this._keyPressHandler);
            this._keyPressHandler = null;
        }
        // Clear auto-start timer on component destroy
        this.clearAutoStartTimer();
    },
    watch: {
        // Watch for tournament state changes and redraw connectors
        tournamentState: {
            handler(newVal, oldVal) {
                this.$nextTick(() => {
                    this.drawBracketConnectors();
                });
            },
            deep: true
        },
        // Keep human_names array in sync when human_count changes
        'newTournament.human_count': {
            handler(newCount) {
                const c = Math.max(0, Math.min(Number(newCount) || 0, 10));
                if (c !== (this.newTournament.human_count || 0)) {
                    this.newTournament.human_count = c;
                }
                const names = this.newTournament.human_names || [];
                while (names.length < c) names.push('');
                this.newTournament.human_names = names.slice(0, c);
            }
        },
        // Phase 4: changing the game mode also updates the map + preset
        'newTournament.game_mode': {
            handler(newMode) {
                this.onGameModeChange(newMode);
            }
        }
    },
    directives: {
        // Auto-focus directive for team name input
        focus: {
            inserted: function (el) {
                el.focus();
            }
        }
    }
};
