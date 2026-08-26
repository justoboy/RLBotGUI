import BotCard from './bot-card-vue.js'
import BotPool from './bot-pool-vue.js'

const HUMAN = {'name': 'Human', 'type': 'human', 'image': 'imgs/human.png'};

export default {
    name: 'tournament',
    template: /*html*/`
    <div class="tournament-page noscroll-flex flex-grow-1">
        <!-- No Tournament State -->
        <div v-if="!tournamentState" class="tournament-empty">
            <div class="tournament-empty-content">
                <h2>Tournament Mode</h2>
                <p>Create a tournament bracket, add participants, and run matches!</p>
                <b-button @click="showCreateModal" variant="success" size="lg">
                    Create New Tournament
                </b-button>
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
                        Round {{ tournamentState.current_round }}
                    </span>
                </div>
                <div class="tournament-actions">
                    <b-button @click="returnToHome" variant="secondary">
                        <b-icon icon="arrow-left"></b-icon> Back
                    </b-button>
                    <b-button @click="saveTournament" variant="info">
                        <b-icon icon="save"></b-icon> Save
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
                            <h5 class="round-title">Round {{ roundIndex + 1 }}</h5>
                            <div class="bracket-round-matches">
                                <div v-for="match in roundMatches" :key="match.match_id" 
                                     class="bracket-match" 
                                     :class="{ 'completed': match.completed, 'active': isMatchActive(match) }"
                                     @click="onMatchClick(match)">
                                    <div class="match-header">
                                        <span class="match-id">{{ match.match_id }}</span>
                                        <span v-if="match.completed" class="match-result">
                                            <b-icon icon="check-circle-fill" variant="success"></b-icon>
                                        </span>
                                    </div>
                                    <div class="match-participant" :class="{ 'winner': match.winner === match.participant1 }">
                                        <span v-if="match.participant1">
                                            {{ match.participant1.name }}
                                        </span>
                                        <span v-else class="placeholder">Waiting...</span>
                                    </div>
                                    <div class="match-vs">VS</div>
                                    <div class="match-participant" :class="{ 'winner': match.winner === match.participant2 }">
                                        <span v-if="match.participant2">
                                            {{ match.participant2.name }}
                                        </span>
                                        <span v-else class="placeholder">Waiting...</span>
                                    </div>
                                    <div v-if="match.score" class="match-score">
                                        <span>{{ match.score[0] }} - {{ match.score[1] }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Participants Panel -->
                <div class="participants-panel">
                    <div class="panel-header">
                        <h4>Participants</h4>
                        <b-button @click="showAddParticipant" variant="outline-success" size="sm" v-if="!tournamentState.completed">
                            <b-icon icon="plus"></b-icon> Add
                        </b-button>
                    </div>
                    <div class="participants-list">
                        <div v-for="participant in tournamentState.participants" :key="participant.participant_id" class="participant-item">
                            <bot-card 
                                :bot="participantToBot(participant)" 
                                :draggable="true"
                                @dragstart="onParticipantDrag(participant)"
                                class="participant-card"
                            />
                            <b-button 
                                @click="removeParticipant(participant.participant_id)" 
                                variant="outline-danger" 
                                size="sm"
                                v-if="!tournamentState.completed"
                            >
                                <b-icon icon="x"></b-icon>
                            </b-button>
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
                        <bot-pool
                            :bots="botPool"
                            :scripts="[]"
                            @bot-clicked="toggleParticipantSelection"
                            :display-human="true"
                            :favorites="[]"
                            :multi-select="true"
                            :selected-bots="selectedParticipants"
                        />
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
                <h4>{{ currentMatch.match_id }}: {{ currentMatch.participant1?.name }} vs {{ currentMatch.participant2?.name }}</h4>
                
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
                    Click a participant to launch the match, then record the winner.
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
        }
    },
    methods: {
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
            try {
                const result = await eel.tournament_save()();
                this.tournamentState = JSON.parse(result);
            } catch (error) {
                console.error('Error saving tournament:', error);
                alert('Error saving tournament: ' + error);
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
        
        async removeParticipant(participantId) {
            try {
                const result = await eel.tournament_remove_participant(participantId)();
                this.tournamentState = JSON.parse(result);
            } catch (error) {
                console.error('Error removing participant:', error);
                alert('Error removing participant: ' + error);
            }
        },
        
        showAddParticipant() {
            alert('Add participant functionality coming soon!');
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
        
        isMatchActive(match) {
            if (match.completed) return false;
            if (match.participant1 && match.participant2) return true;
            return false;
        },
        
        async onMatchClick(match) {
            if (match.completed) return;
            if (!match.participant1 || !match.participant2) return;
            
            // Start the match
            try {
                const configResult = await eel.tournament_start_match(match.match_id)();
                const config = JSON.parse(configResult);
                
                if (config.error) {
                    alert(config.error);
                    return;
                }
                
                // Launch the match
                this.matchInProgress = match.match_id;
                eel.tournament_match_started(match.match_id);
                
                // Store the match for result recording
                this.currentMatch = match;
                this.$bvModal.show('match-result-modal');
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
                    alert(`Tournament Complete! Winner: ${this.tournamentState.winner.name}`);
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
        }
    },
    created() {
        // Load existing tournament if available
        this.loadTournament();
    },
    
    mounted() {
        // Expose methods for Python callbacks
        const self = this;
        
        window.tournamentMatchComplete = function(matchId, winnerName, score) {
            console.log('Match complete:', matchId, winnerName, score);
            // This will be called when match ends
        };
    }
};
