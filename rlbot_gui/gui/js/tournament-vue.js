import BotCard from './bot-card-vue.js'
import BotPool from './bot-pool-vue.js'

const HUMAN = {'name': 'Human', 'type': 'human', 'image': 'imgs/human.png'};

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
                    <b-button @click="showMatchCompleteModal" variant="success" v-if="matchInProgress">
                        <b-icon icon="check-circle"></b-icon> Match Complete
                    </b-button>
                </div>
            </div>

            <!-- Tournament Content -->
            <div class="tournament-content noscroll-flex">
                <!-- Bracket View -->
                <div class="bracket-view noscroll-flex">
                    <div class="bracket-header">
                        <h4>Bracket</h4>
                        <b-button @click="randomizeSeeding" variant="outline-primary" size="sm" v-if="!tournamentState.completed">
                            <b-icon icon="shuffle"></b-icon> Randomize Seeding
                        </b-button>
                    </div>
                    
                    <div class="bracket-tree noscroll-flex">
                        <!-- Group matches by round -->
                        <div v-for="(roundMatches, roundIndex) in matchesByRound" :key="roundIndex" class="bracket-round">
                            <h5 class="round-title">{{ getRoundName(roundMatches[0]?.round_num, roundMatches) }}</h5>
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
                        <b-form-select-option value="double_elimination">Double Elimination (Coming Soon)</b-form-select-option>
                        <b-form-select-option value="round_robin">Round Robin (Coming Soon)</b-form-select-option>
                    </b-form-select>
                </b-form-group>

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
    },
    data() {
        return {
            tournamentState: null,
            botPool: [],
            selectedParticipants: [],
            newTournament: {
                name: '',
                format: 'single_elimination'
            },
            currentMatch: null,
            matchInProgress: null,
            savedTournaments: [],
            isSaving: false,
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
                    JSON.stringify(this.selectedParticipants)
                )();
                
                this.tournamentState = JSON.parse(result);
                this.selectedParticipants = [];
                this.newTournament = { name: '', format: 'single_elimination' };
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
