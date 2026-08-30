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
                mutators: { ...DEFAULT_MUTATORS }
            },
            currentMatch: null,
            matchInProgress: null,
            savedTournaments: [],
            isSaving: false,
            MUTATOR_OPTIONS: MUTATOR_OPTIONS,
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
        };
    },
    computed: {
        formatLabel() {
            if (!this.tournamentState) return '';
            const labels = {
                'single_elimination': 'Single Elimination',
                'double_elimination': 'Double Elimination',
                'round_robin': 'Round Robin'
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
  
            return Object.values(rounds);
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
            return this.tournamentState.losers_bracket_matches || [];
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
            
            return Object.values(rounds);
        },
        // Butterfly layout: split each round into a left wing and a right wing,
        // with the final round (1 match) in the center.
        // Left wing: rounds 1..n-1 in ascending order (outer â†’ inner).
        // Right wing: rounds n-1..1 in descending order (inner â†’ outer).
        butterflyRounds() {
            if (!this.tournamentState || !this.tournamentState.matches) {
                return { left: [], center: null, right: [] };
            }
            
            const rounds = {};
            for (const match of this.tournamentState.matches) {
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
        // Each wing's round 1 is spread evenly across the full height; every later
        // round is placed at the midpoint of the matches that feed into it.
        wbMatchPositions() {
            if (!this.tournamentState || !this.tournamentState.matches) return {};
            const { left, center, right } = this.butterflyRounds;
            const positions = {};
            for (const wing of [left, right]) {
                // Flatten all matches in this wing and compute positions
                const wingMatches = wing.flatMap(round => round.matches);
                Object.assign(positions, this.computeBracketPositions(wingMatches));
            }
            if (center) {
                positions[center.matches[0].match_id] = 50;
            }
            return positions;
        },
        lbMatchPositions() {
            if (!this.tournamentState || !this.losersBracketMatches) return {};
            return this.computeBracketPositions(this.losersBracketMatches);
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
                    this.drawSectionConnectors(wbSvg, wbScrollContainer, this.tournamentState.matches, 'rgba(0, 217, 255, 0.55)');
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

        getRoundName(roundNum, roundMatches) {
            if (!roundNum || !roundMatches) return `Round ${roundNum || 1}`;
            
            // Get total number of rounds
            if (!this.tournamentState || !this.tournamentState.matches) {
                return `Round ${roundNum}`;
            }
            
            // Find total rounds by getting the max round number
            const allRounds = new Set(this.tournamentState.matches.map(m => m.round_num));
            const totalRounds = Math.max(...allRounds);
            
            // Calculate this round's position from the end
            const roundsFromEnd = totalRounds - roundNum + 1;
            
            // Name the last few rounds specially
            if (roundsFromEnd === 1) {
                return 'Finals';
            } else if (roundsFromEnd === 2) {
                return 'Semi-Finals';
            } else if (roundsFromEnd === 3) {
                return 'Quarter-Finals';
            } else {
                return `Round ${roundNum}`;
            }
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
                const roundMatches = matchesByRoundNum[roundNum];
                const hasIncomplete = roundMatches.some(m => !m.completed);
                if (hasIncomplete) {
                    return this.getRoundName(roundNum, roundMatches);
                }
            }
            
            // All rounds complete - show the final round name
            const lastRound = roundNumbers[roundNumbers.length - 1];
            return this.getRoundName(lastRound, matchesByRoundNum[lastRound]);
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

            try {
                console.log('[Tournament] Calling eel.tournament_new...');
                const result = await eel.tournament_new(
                    this.newTournament.name,
                    this.newTournament.format,
                    JSON.stringify(allParticipants),
                    JSON.stringify(this.newTournament.mutators),
                    teamSize,
                    allowDuplicates
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
                this.newTournament = { name: '', format: 'single_elimination', team_size: 1, allow_duplicates: false, human_count: 0, human_names: [], mutators: { ...DEFAULT_MUTATORS } };
                this.refreshTeamBalance();
                this.refreshStats();
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

        winnerDisplayName() {
            if (!this.tournamentState) return '';
            if (this.tournamentState.winner_team) return this.tournamentState.winner_team.name;
            if (this.tournamentState.winner) return this.tournamentState.winner.name;
            return '';
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
        
        showMatchCompleteModal() {
            if (!this.currentMatch) return;
            this.$bvModal.show('match-result-modal');
        },
        
        async onMatchClick(match) {
            if (match.completed) return;
            if (!match.participant1 || !match.participant2) return;

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
            console.log('[Tournament] loadSavedTournaments called');
            // Load list of saved tournaments from backend
            try {
                if (eel.tournament_get_saved_list) {
                    const saved = eel.tournament_get_saved_list()();
                    saved.then(result => {
                        const parsed = JSON.parse(result);
                        console.log('[Tournament] Saved tournaments loaded:', parsed.length, 'items');
                        this.savedTournaments = parsed;
                    });
                } else {
                    console.error('[Tournament] eel.tournament_get_saved_list is not defined');
                }
            } catch (error) {
                console.error('[Tournament] Error loading saved tournaments:', error);
                this.savedTournaments = [];
            }
        },
        
        loadSavedTournament(tournament) {
            console.log('[Tournament] loadSavedTournament called for:', tournament.name, tournament.tournament_id);
            // Load the tournament from backend by ID
            if (eel.tournament_load_from_id) {
                eel.tournament_load_from_id(tournament.tournament_id)().then(result => {
                    console.log('[Tournament] load_from_id returned:', result.substring(0, 200));
                    const state = JSON.parse(result);
                    if (state.error) {
                        console.error('[Tournament] Error from backend:', state.error);
                        alert('Error loading tournament: ' + state.error);
                    } else {
                        console.log('[Tournament] Setting tournamentState from loadSavedTournament:', state.name);
                        console.log('[Tournament] Before: tournamentState was', this.tournamentState ? this.tournamentState.name : 'null');
                        this.tournamentState = state;
                        console.log('[Tournament] After: tournamentState is', this.tournamentState ? this.tournamentState.name : 'null');
                        this.refreshTeamBalance();
                        this.refreshStats();
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
                'round_robin': 'Round Robin'
            };
            return labels[format] || format;
        },
        
        resetMutatorsToDefault() {
            this.newTournament.mutators = { ...DEFAULT_MUTATORS };
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
                        this.tournamentState = currentState;
                        this.matchInProgress = null;
                        this.currentMatch = null;
                        clearInterval(pollInterval);
                        this.refreshTeamBalance();
                        this.refreshStats();
                    }
                } catch (e) {
                    console.log('Polling error:', e);
                }
            }, 1000);
            setTimeout(() => { clearInterval(pollInterval); }, 300000);
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
        console.log('[Tournament] mounted() called');
        console.log('[Tournament] this.tournamentState =', this.tournamentState ? this.tournamentState.name : 'null');
        console.log('[Tournament] this.$el =', this.$el ? this.$el.outerHTML.substring(0, 200) : 'null');
        // Draw bracket connectors after initial render
        this.$nextTick(() => {
            this.drawBracketConnectors();
        });
        // Redraw connectors when the window resizes
        this._bracketResizeHandler = () => this.drawBracketConnectors();
        window.addEventListener('resize', this._bracketResizeHandler);
    },
    beforeDestroy() {
        if (this._bracketResizeHandler) {
            window.removeEventListener('resize', this._bracketResizeHandler);
            this._bracketResizeHandler = null;
        }
    },
    watch: {
        // Watch for tournament state changes and redraw connectors
        tournamentState: {
            handler(newVal, oldVal) {
                console.log('[Tournament] tournamentState changed: old=', oldVal ? oldVal.name : 'null', 'new=', newVal ? newVal.name : 'null');
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
        }
    }
};
