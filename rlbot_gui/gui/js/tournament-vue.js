import BotCard from './bot-card-vue.js'
import BotPool from './bot-pool-vue.js'
import MutatorField from './mutator-field-vue.js'

const HUMAN = {'name': 'Human', 'type': 'human', 'image': 'imgs/human.png'};

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
    template: /*html*/`
    <div class="tournament-page noscroll-flex flex-grow-1">
        <!-- Landing Page - Show when no tournament is active -->
        <div v-if="!tournamentState" class="tournament-landing noscroll-flex flex-grow-1">
            <div class="tournament-landing-content">
                <div class="landing-header">
                    <h2>Tournament Mode</h2>
                    <b-button @click="returnToHome" variant="secondary">
                        <b-icon icon="arrow-left"></b-icon> Back to Main
                    </b-button>
                </div>
                
                <p class="landing-description">Create a tournament bracket, add participants, and run matches!</p>
                
                <div class="saved-tournaments">
                    <h4 v-if="savedTournaments.length > 0">Saved Tournaments</h4>
                    <div v-if="savedTournaments.length === 0" class="no-saved-tournaments">
                        <p>No saved tournaments found.</p>
                    </div>
                    <div v-else class="saved-tournaments-list">
                        <div
                            v-for="tournament in savedTournaments"
                            :key="tournament.tournament_id"
                            class="saved-tournament-card"
                            @click="loadSavedTournament(tournament)"
                        >
                            <div class="tournament-info-card">
                                <h5>{{ tournament.name }}</h5>
                                <span class="tournament-format-badge">{{ formatLabelFromData(tournament.format) }}</span>
                                <span class="tournament-participants">{{ tournament.participants?.length || 0 }} participants</span>
                                <span v-if="tournament.completed" class="tournament-completed">
                                    <b-icon icon="trophy-fill" variant="warning"></b-icon> Completed
                                </span>
                                <span v-else class="tournament-in-progress">In Progress</span>
                            </div>
                            <div class="tournament-actions-card">
                                <b-button @click.stop="loadSavedTournament(tournament)" variant="primary" size="sm">
                                    Load
                                </b-button>
                                <b-button @click.stop="deleteSavedTournament(tournament.tournament_id)" variant="danger" size="sm">
                                    <b-icon icon="trash"></b-icon>
                                </b-button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="create-new-section">
                    <b-button @click="showCreateModal" variant="success" size="lg">
                        <b-icon icon="plus-circle"></b-icon> Create New Tournament
                    </b-button>
                </div>
                
                <!-- Import/Export Section -->
                <div class="import-export-section mt-3">
                    <b-button @click="triggerImportFilePicker" variant="secondary" size="sm" class="mr-2">
                        <b-icon icon="upload"></b-icon> Import Tournament
                    </b-button>
                    <b-button @click="exportTournament" variant="secondary" size="sm" v-if="tournamentState">
                        <b-icon icon="download"></b-icon> Export Tournament
                    </b-button>
                </div>

                <!-- Hidden file input for importing tournament JSON files -->
                <input type="file" ref="importFileInput" accept=".json,application/json" style="display:none" @change="handleImportFileSelected">
            </div>
        </div>

        <!-- Tournament Active -->
        <div v-else class="tournament-active noscroll-flex flex-grow-1">
            <!-- Tournament Header -->
            <div class="tournament-header">
                <div class="tournament-info">
                    <h3>{{ tournamentState.name }}</h3>
                    <span class="tournament-format">{{ formatLabel }}</span>
                    <span class="tournament-status" v-if="tournamentState.completed">
                        <b-icon icon="trophy-fill" variant="warning"></b-icon>
                        Winner: {{ tournamentState.winner.name }}
                    </span>
                    <span class="tournament-status" v-else>
                        {{ getCurrentRoundName() }}
                    </span>
                </div>
                <div class="tournament-actions">
                    <b-button @click="returnToLanding" variant="secondary">
                        <b-icon icon="arrow-left"></b-icon> Back
                    </b-button>
                    <b-button @click="saveTournament" variant="info" v-if="!matchInProgress">
                        <b-icon :icon="isSaving ? 'check-circle-fill' : 'save'"></b-icon>
                        {{ isSaving ? 'Saved!' : 'Save' }}
                    </b-button>
                    <b-button @click="exportTournament" variant="secondary" v-if="!matchInProgress">
                        <b-icon icon="download"></b-icon> Export
                    </b-button>
                    <b-button @click="showMatchCompleteModal" variant="success" v-if="matchInProgress">
                        <b-icon icon="check-circle"></b-icon> Match Complete
                    </b-button>
                </div>
            </div>

            <!-- Tournament Content -->
            <div class="tournament-content noscroll-flex">
                <!-- Bracket View for Single/Double Elimination -->
                <div class="bracket-view noscroll-flex" v-if="tournamentState.format !== 'round_robin'">
                    <div class="bracket-header">
                        <h4>{{ formatLabel }} Bracket</h4>
                        <b-button @click="randomizeSeeding" variant="outline-primary" size="sm" v-if="!tournamentState.completed">
                            <b-icon icon="shuffle"></b-icon> Randomize Seeding
                        </b-button>
                    </div>
                    
                    <div class="bracket-tree noscroll-flex">
                        <!-- Winners Bracket -->
                        <div class="bracket-section">
                            <h5 class="section-title">Winners Bracket</h5>
                            <div v-for="(roundMatches, roundIndex) in matchesByRound" :key="roundIndex" class="bracket-round">
                                <h6 class="round-title">{{ getRoundName(roundMatches[0]?.round_num, roundMatches) }}</h6>
                                <div class="bracket-round-matches">
                                    <div v-for="match in roundMatches" :key="match.match_id" 
                                         class="bracket-match" 
                                         :class="{ 'completed': match.completed, 'active': isMatchActive(match), 'in-progress': isMatchInProgress(match) }"
                                         @click="onMatchClick(match)">
                                        <div class="match-header">
                                            <span class="match-id">{{ match.match_id }}</span>
                                            <span v-if="match.completed" class="match-result">
                                                <b-icon icon="check-circle-fill" variant="success"></b-icon>
                                            </span>
                                            <span v-else-if="isMatchInProgress(match)" class="match-in-progress">
                                                <b-icon icon="hourglass-split" variant="info"></b-icon> In Progress
                                            </span>
                                        </div>
                                        <div class="match-players">
                                            <span v-if="match.participant1">{{ match.participant1.name }}</span>
                                            <span v-else class="placeholder">Waiting...</span>
                                            <span class="match-vs-inline">vs</span>
                                            <span v-if="match.participant2">{{ match.participant2.name }}</span>
                                            <span v-else class="placeholder">Waiting...</span>
                                        </div>
                                        <div v-if="match.score" class="match-score">
                                            {{ match.score[0] }} - {{ match.score[1] }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Losers Bracket for Double Elimination -->
                        <div class="bracket-section" v-if="tournamentState.format === 'double_elimination' && losersBracketMatches.length > 0">
                            <h5 class="section-title">Losers Bracket</h5>
                            <div v-for="(roundMatches, roundIndex) in losersBracketMatchesByRound" :key="'lb-' + roundIndex" class="bracket-round">
                                <h6 class="round-title">Losers Round {{ roundIndex + 1 }}</h6>
                                <div class="bracket-round-matches">
                                    <div v-for="match in roundMatches" :key="match.match_id" 
                                         class="bracket-match losers-match"
                                         :class="{ 'completed': match.completed, 'active': isMatchActive(match), 'in-progress': isMatchInProgress(match) }"
                                         @click="onMatchClick(match)">
                                        <div class="match-header">
                                            <span class="match-id">{{ match.match_id }}</span>
                                            <span v-if="match.completed" class="match-result">
                                                <b-icon icon="check-circle-fill" variant="success"></b-icon>
                                            </span>
                                            <span v-else-if="isMatchInProgress(match)" class="match-in-progress">
                                                <b-icon icon="hourglass-split" variant="info"></b-icon> In Progress
                                            </span>
                                        </div>
                                        <div class="match-players">
                                            <span v-if="match.participant1">{{ match.participant1.name }}</span>
                                            <span v-else class="placeholder">Waiting...</span>
                                            <span class="match-vs-inline">vs</span>
                                            <span v-if="match.participant2">{{ match.participant2.name }}</span>
                                            <span v-else class="placeholder">Waiting...</span>
                                        </div>
                                        <div v-if="match.score" class="match-score">
                                            {{ match.score[0] }} - {{ match.score[1] }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Round Robin View -->
                <div class="round-robin-view noscroll-flex" v-else>
                    <div class="round-robin-header">
                        <h4>Round Robin Standings</h4>
                    </div>
                    
                    <!-- Matches List -->
                    <div class="round-robin-matches">
                        <h5>Matches</h5>
                        <div class="matches-list">
                            <div v-for="match in tournamentState.matches" :key="match.match_id" 
                                 class="round-robin-match"
                                 :class="{ 'completed': match.completed, 'active': isMatchActive(match), 'in-progress': isMatchInProgress(match) }"
                                 @click="onMatchClick(match)">
                                <div class="match-info">
                                    <span class="match-id">{{ match.match_id }}</span>
                                    <span class="match-pair">
                                        {{ match.participant1?.name || 'Waiting' }} vs {{ match.participant2?.name || 'Waiting' }}
                                    </span>
                                </div>
                                <div class="match-result" v-if="match.completed">
                                    <span class="match-score">{{ match.score?.[0] }} - {{ match.score?.[1] }}</span>
                                    <b-icon icon="check-circle-fill" variant="success"></b-icon>
                                </div>
                                <div class="match-status" v-else-if="isMatchInProgress(match)">
                                    <b-icon icon="hourglass-split" variant="info"></b-icon> In Progress
                                </div>
                                <div class="match-status" v-else>
                                    <span>Pending</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Standings Table -->
                    <div class="round-robin-standings">
                        <h5>Standings</h5>
                        <table class="standings-table">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Participant</th>
                                    <th>Played</th>
                                    <th>Wins</th>
                                    <th>Draws</th>
                                    <th>Losses</th>
                                    <th>Goals For</th>
                                    <th>Goals Against</th>
                                    <th>Goal Difference</th>
                                    <th>Points</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(standing, index) in standings" :key="standing.participant.participant_id">
                                    <td>{{ index + 1 }}</td>
                                    <td class="participant-name">{{ standing.participant.name }}</td>
                                    <td>{{ standing.played }}</td>
                                    <td>{{ standing.wins }}</td>
                                    <td>{{ standing.draws }}</td>
                                    <td>{{ standing.losses }}</td>
                                    <td>{{ standing.goals_for }}</td>
                                    <td>{{ standing.goals_against }}</td>
                                    <td>{{ standing.goal_difference }}</td>
                                    <td class="points">{{ standing.points }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Tournament Modal -->
        <b-modal id="create-tournament-modal" title="Create Tournament" size="lg" hide-footer centered>
            <b-form @submit.prevent="createTournament">
                <b-form-group label="Tournament Name" label-for="tournament-name">
                    <b-form-input 
                        id="tournament-name" 
                        v-model="newTournament.name" 
                        placeholder="Enter tournament name"
                        required
                    ></b-form-input>
                </b-form-group>

                <b-form-group label="Format" label-for="tournament-format">
                    <b-form-select 
                        id="tournament-format" 
                        v-model="newTournament.format"
                    >
                        <b-form-select-option value="single_elimination">Single Elimination</b-form-select-option>
                        <b-form-select-option value="double_elimination">Double Elimination</b-form-select-option>
                        <b-form-select-option value="round_robin">Round Robin</b-form-select-option>
                    </b-form-select>
                </b-form-group>

                <!-- Mutator Settings -->
                <div class="mutator-settings-section">
                    <h5>Match Settings (Optional)</h5>
                    <p class="text-muted small">Customize match settings. Leave as default for standard matches.</p>
                    
                    <div class="mutator-grid">
                        <mutator-field
                            label="Match Length"
                            :options="MUTATOR_OPTIONS.match_length"
                            v-model="newTournament.mutators.match_length"
                        />
                        <mutator-field
                            label="Max Score"
                            :options="MUTATOR_OPTIONS.max_score"
                            v-model="newTournament.mutators.max_score"
                        />
                        <mutator-field
                            label="Overtime"
                            :options="MUTATOR_OPTIONS.overtime"
                            v-model="newTournament.mutators.overtime"
                        />
                        <mutator-field
                            label="Series Length"
                            :options="MUTATOR_OPTIONS.series_length"
                            v-model="newTournament.mutators.series_length"
                        />
                        <mutator-field
                            label="Game Speed"
                            :options="MUTATOR_OPTIONS.game_speed"
                            v-model="newTournament.mutators.game_speed"
                        />
                        <mutator-field
                            label="Boost Amount"
                            :options="MUTATOR_OPTIONS.boost_amount"
                            v-model="newTournament.mutators.boost_amount"
                        />
                        <mutator-field
                            label="Rumble"
                            :options="MUTATOR_OPTIONS.rumble"
                            v-model="newTournament.mutators.rumble"
                        />
                        <mutator-field
                            label="Demolish"
                            :options="MUTATOR_OPTIONS.demolish"
                            v-model="newTournament.mutators.demolish"
                        />
                    </div>
                    
                    <b-button @click="resetMutatorsToDefault" variant="outline-secondary" size="sm" class="mt-2">
                        <b-icon icon="arrow-counterclockwise"></b-icon> Reset to Defaults
                    </b-button>
                </div>

                <b-form-group label="Select Participants from Pool" label-for="participant-pool">
                    <div class="participant-pool-selection">
                        <div class="bot-pool-wrapper">
                            <bot-card
                                v-for="bot in botPool"
                                :key="bot.participant_id || bot.path"
                                :bot="bot"
                                :draggable="false"
                                class="tournament-bot-card"
                                :class="{ 'selected': isParticipantSelected(bot) }"
                                @click="toggleParticipantSelection(bot)"
                            />
                        </div>
                    </div>
                </b-form-group>

                <div class="selected-participants">
                    <h5>Selected ({{ selectedParticipants.length }})</h5>
                    <div class="selected-list">
                        <b-badge 
                            v-for="p in selectedParticipants" 
                            :key="p.participant_id"
                            variant="primary"
                            class="m-1"
                        >
                            {{ p.name }}
                            <b-icon icon="x-circle" @click="toggleParticipantSelection(p)" style="cursor: pointer; margin-left: 5px;"></b-icon>
                        </b-badge>
                    </div>
                </div>

                <div class="modal-footer mt-3">
                    <b-button @click="$bvModal.hide('create-tournament-modal')" variant="secondary">Cancel</b-button>
                    <b-button 
                        @click="createTournament" 
                        variant="success"
                        :disabled="selectedParticipants.length < 2"
                    >
                        Generate Bracket
                    </b-button>
                </div>
            </b-form>
        </b-modal>

        <!-- Match Result Modal -->
        <b-modal id="match-result-modal" title="Match Result" centered hide-footer>
            <div v-if="currentMatch">
                <h4>{{ currentMatch.participant1?.name }} vs {{ currentMatch.participant2?.name }}</h4>
                
                <div class="match-result-options">
                    <b-button 
                        @click="recordWinner(currentMatch.participant1.name, 1, 0)" 
                        variant="success"
                        size="lg"
                        class="m-2"
                    >
                        {{ currentMatch.participant1.name }} Wins
                    </b-button>
                    <b-button 
                        @click="recordWinner(currentMatch.participant2.name, 0, 1)" 
                        variant="success"
                        size="lg"
                        class="m-2"
                    >
                        {{ currentMatch.participant2.name }} Wins
                    </b-button>
                </div>

                <b-alert show variant="info">
                    Match has ended. Click the winner to record the result.
                </b-alert>
            </div>
            <div class="modal-footer">
                <b-button @click="currentMatch = null; $bvModal.hide('match-result-modal')" variant="secondary">Cancel</b-button>
            </div>
        </b-modal>
    </div>
    `,
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
                mutators: { ...DEFAULT_MUTATORS }
            },
            currentMatch: null,
            matchInProgress: null,
            savedTournaments: [],
            isSaving: false,
            MUTATOR_OPTIONS: MUTATOR_OPTIONS,
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
        standings() {
            if (!this.tournamentState || this.tournamentState.format !== 'round_robin') return [];
            
            // Calculate standings from matches
            const standings = {};
            
            // Initialize standings for all participants
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
            
            // Process completed matches
            for (const match of this.tournamentState.matches) {
                if (!match.completed || !match.score) continue;
                if (!match.participant1 || !match.participant2) continue;
                
                const p1Id = match.participant1.participant_id;
                const p2Id = match.participant2.participant_id;
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
            await this.loadBotPool();
            this.$bvModal.show('create-tournament-modal');
        },
        
        async loadBotPool() {
            // Load bots from the main pool
            const response = await fetch('js/bot-pool-vue.js');
            // We'll use a simpler approach - get bots from eel
            if (eel.get_tournament_bots) {
                this.botPool = await eel.get_tournament_bots()();
            } else {
                // Default to human if no bots available
                this.botPool = [HUMAN];
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
        
        async createTournament() {
            if (this.selectedParticipants.length < 2) {
                alert('Please select at least 2 participants');
                return;
            }
            
            // Check for duplicate tournament name
            const existingTournament = this.savedTournaments.find(
                t => t.name.toLowerCase() === this.newTournament.name.toLowerCase()
            );
            if (existingTournament) {
                alert(`A tournament named "${this.newTournament.name}" already exists. Please choose a different name.`);
                return;
            }
            
            try {
                const result = await eel.tournament_new(
                    this.newTournament.name,
                    this.newTournament.format,
                    JSON.stringify(this.selectedParticipants),
                    JSON.stringify(this.newTournament.mutators)
                )();
            
                this.tournamentState = JSON.parse(result);
                this.selectedParticipants = [];
                this.newTournament = { name: '', format: 'single_elimination', mutators: { ...DEFAULT_MUTATORS } };
                this.$bvModal.hide('create-tournament-modal');
            } catch (error) {
                console.error('Error creating tournament:', error);
                alert('Error creating tournament: ' + error);
            }
        },
        
        async loadTournament() {
            try {
                const result = await eel.tournament_load()();
                if (result) {
                    this.tournamentState = JSON.parse(result);
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
            
            // Start the match - it will launch automatically and record the winner
            try {
                const result = await eel.tournament_start_match(match.match_id)();
                const response = JSON.parse(result);
              
                if (response.error) {
                    alert(response.error);
                    return;
                }
              
                // Match is launching - show in progress indicator
                this.matchInProgress = match.match_id;
                this.currentMatch = match;
                
                // Poll for tournament state update (match completion)
                const pollInterval = setInterval(async () => {
                    try {
                        // Fetch fresh state from backend on each poll
                        const freshState = await eel.tournament_get_state()();
                        if (!freshState) {
                            console.log('Polling: No state returned');
                            return;
                        }
                        
                        const currentState = JSON.parse(freshState);
                        
                        // Check both matches and losers_bracket_matches
                        let updatedMatch = null;
                        if (currentState.matches && Array.isArray(currentState.matches)) {
                            updatedMatch = currentState.matches.find(m => m.match_id === match.match_id);
                        }
                        if (!updatedMatch && currentState.losers_bracket_matches && Array.isArray(currentState.losers_bracket_matches)) {
                            updatedMatch = currentState.losers_bracket_matches.find(m => m.match_id === match.match_id);
                        }

                        if (updatedMatch && updatedMatch.completed) {
                            // Match completed - update the tournament state
                            this.tournamentState = currentState;
                            this.matchInProgress = null;
                            this.currentMatch = null;
                            clearInterval(pollInterval);
                            console.log('Match completed, tournament completed:', currentState.completed);

                            // Check if tournament is complete - just update state, no alert needed
                            if (currentState.completed) {
                                console.log('Tournament Complete! Winner:', currentState.winner.name);
                            }
                        }
                    } catch (e) {
                        console.log('Polling error:', e);
                    }
                }, 1000);
                
                // Stop polling after 5 minutes
                setTimeout(() => {
                    clearInterval(pollInterval);
                }, 300000);
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
                }
            } catch (error) {
                console.error('Error loading saved tournaments:', error);
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
                    }
                });
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
                alert('Tournament imported successfully!');
            } catch (error) {
                console.error('Error importing tournament:', error);
                alert('Invalid JSON format: ' + error);
            }
        }
    },
    created() {
        // Load saved tournaments list
        this.loadSavedTournaments();
        // Load existing tournament if available
        this.loadTournament();
    },
    
    mounted() {
        // No callbacks needed - match completion is detected via polling
    }
};
