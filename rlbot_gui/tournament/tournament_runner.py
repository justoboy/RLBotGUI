"""
Manages tournament state and execution
"""
import json
import uuid
from typing import List, Dict, Any, Optional

import eel
from PyQt5.QtCore import QSettings

from rlbot_gui.tournament.tournament_state import TournamentState, Participant, Match, Team
from rlbot_gui.tournament.bracket_generator import (
    generate_single_elimination_bracket,
    generate_double_elimination_bracket,
    generate_round_robin_bracket
)
from rlbot_gui.tournament.team_manager import (
    validate_team_formation,
    form_teams_random,
    form_teams_seeded,
    form_teams_manual,
    generate_team_bracket,
    build_match_bot_list,
    team_balance_report
)

# Global state for current tournament
CURRENT_TOURNAMENT: Optional[TournamentState] = None


def generate_match_config_from_match(match: Match, tournament_format: str) -> Dict[str, Any]:
    """
    Generate match configuration for RLBot based on tournament match.
    """
    if match.participant1 is None or match.participant2 is None:
        raise ValueError("Match must have two participants")
    
    # Build team configurations
    blue_team = []
    orange_team = []
    
    # Add participant 1 to blue team
    if match.participant1.participant_type == 'human':
        blue_team.append({
            'name': match.participant1.name,
            'team': 0,
            'type': 'human'
        })
    else:
        blue_team.append({
            'name': match.participant1.name,
            'team': 0,
            'type': 'bot',
            'path': match.participant1.bot_config.get('path', '') if match.participant1.bot_config else '',
            'config_name': match.participant1.bot_config.get('config_name', '') if match.participant1.bot_config else ''
        })
    
    # Add participant 2 to orange team
    if match.participant2.participant_type == 'human':
        orange_team.append({
            'name': match.participant2.name,
            'team': 1,
            'type': 'human'
        })
    else:
        orange_team.append({
            'name': match.participant2.name,
            'team': 1,
            'type': 'bot',
            'path': match.participant2.bot_config.get('path', '') if match.participant2.bot_config else '',
            'config_name': match.participant2.bot_config.get('config_name', '') if match.participant2.bot_config else ''
        })
    
    return {
        'blue_team': blue_team,
        'orange_team': orange_team,
        'map': 'DFHStadium',  # Default map
        'game_mode': 'soccer'
    }


@eel.expose
def tournament_new(name: str, tournament_format: str, participants_json: str, match_settings_json: str = '{}', team_size: int = 1) -> str:
    """
    Create a new tournament.
    
    Args:
        name: Tournament name
        tournament_format: 'single_elimination', 'double_elimination', or 'round_robin'
        participants_json: JSON string of participant list
        match_settings_json: JSON string of match settings (optional)
        team_size: Participants per team (1, 2, 3, or 4). Default 1 (1v1).
    
    Returns:
        JSON string of tournament state
    """
    global CURRENT_TOURNAMENT
    
    participants_data = json.loads(participants_json)
    participants = [Participant.from_dict(p) for p in participants_data]
    
    # Parse match settings
    match_settings = json.loads(match_settings_json) if match_settings_json else {}
    
    # Validate team size
    if team_size not in (1, 2, 3, 4):
        return json.dumps({'error': f'Team size must be 1, 2, 3, or 4 (got {team_size})'})
    
    # Validate participant count for team formation
    if team_size > 1:
        valid, error_msg = validate_team_formation(len(participants), team_size)
        if not valid:
            return json.dumps({'error': error_msg})
    
    tournament_id = str(uuid.uuid4())[:8]
    
    CURRENT_TOURNAMENT = TournamentState(
        name=name,
        tournament_id=tournament_id,
        format=tournament_format,
        participants=participants,
        match_settings=match_settings,
        team_size=team_size
    )
    
    if team_size > 1:
        # Form teams (random assignment by default) and generate team bracket
        teams = form_teams_random(participants, team_size)
        CURRENT_TOURNAMENT.teams = teams
        matches, losers_matches = generate_team_bracket(teams, tournament_format)
        CURRENT_TOURNAMENT.matches = matches
        CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
    else:
        # 1v1: existing participant-based bracket
        if tournament_format == 'single_elimination':
            matches, num_rounds = generate_single_elimination_bracket(participants)
            CURRENT_TOURNAMENT.matches = matches
        elif tournament_format == 'double_elimination':
            winners_matches, losers_matches, num_rounds = generate_double_elimination_bracket(participants)
            CURRENT_TOURNAMENT.matches = winners_matches
            CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
        elif tournament_format == 'round_robin':
            matches = generate_round_robin_bracket(participants)
            CURRENT_TOURNAMENT.matches = matches
    
    CURRENT_TOURNAMENT.current_round = 1
    return tournament_save_state()


@eel.expose
def tournament_form_teams(assignment_method: str = 'random', team_names_json: str = '[]') -> str:
    """
    (Re)form teams from the current tournament's participants.

    Args:
        assignment_method: 'random', 'seeded', or 'manual'
        team_names_json: JSON list of optional custom team names

    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    team_size = CURRENT_TOURNAMENT.team_size
    if team_size <= 1:
        return json.dumps({'error': 'Team formation only applies when team size > 1'})

    participants = CURRENT_TOURNAMENT.participants
    valid, error_msg = validate_team_formation(len(participants), team_size)
    if not valid:
        return json.dumps({'error': error_msg})

    if assignment_method == 'seeded':
        teams = form_teams_seeded(participants, team_size)
    elif assignment_method == 'manual':
        # Manual assignment is done client-side via tournament_set_team_members
        return json.dumps({'error': 'Use tournament_set_team_members for manual assignment'})
    else:
        teams = form_teams_random(participants, team_size)

    # Apply custom names if provided
    try:
        names = json.loads(team_names_json) if team_names_json else []
    except (json.JSONDecodeError, TypeError):
        names = []
    for i, team in enumerate(teams):
        if i < len(names) and names[i]:
            team.name = names[i]

    CURRENT_TOURNAMENT.teams = teams

    # Regenerate the bracket with the new teams
    matches, losers_matches = generate_team_bracket(teams, CURRENT_TOURNAMENT.format)
    CURRENT_TOURNAMENT.matches = matches
    CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
    CURRENT_TOURNAMENT.current_round = 1
    CURRENT_TOURNAMENT.completed = False
    CURRENT_TOURNAMENT.winner = None
    CURRENT_TOURNAMENT.winner_team = None

    return tournament_save_state()


@eel.expose
def tournament_set_team_members(team_index: int, participants_json: str, team_name: str = '') -> str:
    """
    Manually set the members of a specific team.

    Args:
        team_index: 0-based index of the team
        participants_json: JSON list of participant dicts (must match team_size)
        team_name: Optional custom name for the team

    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    team_size = CURRENT_TOURNAMENT.team_size
    if team_size <= 1:
        return json.dumps({'error': 'Team management only applies when team size > 1'})

    members_data = json.loads(participants_json)
    members = [Participant.from_dict(p) for p in members_data]

    if len(members) != team_size:
        return json.dumps({'error': f'Team must have exactly {team_size} members (got {len(members)})'})

    # Ensure all members are part of the tournament's participant pool
    pool_ids = {p.participant_id for p in CURRENT_TOURNAMENT.participants}
    for m in members:
        if m.participant_id not in pool_ids:
            return json.dumps({'error': f"Participant '{m.name}' is not in the tournament pool"})

    # Ensure no participant is on two teams
    assigned = set()
    for i, team in enumerate(CURRENT_TOURNAMENT.teams):
        if i == team_index:
            continue
        for p in team.participants:
            assigned.add(p.participant_id)
    for m in members:
        if m.participant_id in assigned:
            return json.dumps({'error': f"Participant '{m.name}' is already on another team"})

    if team_index >= len(CURRENT_TOURNAMENT.teams):
        return json.dumps({'error': f'Team index {team_index} out of range'})

    CURRENT_TOURNAMENT.teams[team_index].participants = members
    if team_name:
        CURRENT_TOURNAMENT.teams[team_index].name = team_name

    return tournament_save_state()


@eel.expose
def tournament_team_balance() -> str:
    """
    Get a team balance report for the current tournament.

    Returns:
        JSON string with balance info
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    if not CURRENT_TOURNAMENT.teams:
        return json.dumps({'balanced': True, 'spread': 0.0, 'strengths': {}})

    return json.dumps(team_balance_report(CURRENT_TOURNAMENT.teams))


@eel.expose
def tournament_load() -> Optional[str]:
    """
    Load a previous tournament save if available.
    
    Returns:
        JSON string of tournament state or None
    """
    global CURRENT_TOURNAMENT
    
    settings = QSettings("rlbotgui", "tournament_save")
    state = settings.value("save")
    
    if state:
        state_dict = json.loads(state)
        CURRENT_TOURNAMENT = TournamentState.from_dict(state_dict)
        return tournament_save_state()
    
    return None


@eel.expose
def tournament_save() -> str:
    """
    Save current tournament state.
    
    Returns:
        JSON string of tournament state
    """
    return tournament_save_state()


@eel.expose
def tournament_save_state() -> str:
    """
    Save tournament state to QSettings and return JSON.
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    settings = QSettings("rlbotgui", "tournament_save")
    serialized = CURRENT_TOURNAMENT.to_dict()
    settings.setValue("save", json.dumps(serialized))
    
    return json.dumps(serialized)


@eel.expose
def tournament_delete() -> None:
    """
    Delete the current tournament save.
    """
    global CURRENT_TOURNAMENT
    
    CURRENT_TOURNAMENT = None
    QSettings("rlbotgui", "tournament_save").remove("save")


@eel.expose
def tournament_get_state() -> Optional[str]:
    """
    Get current tournament state.
    
    Returns:
        JSON string of tournament state or None
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return None
    
    return json.dumps(CURRENT_TOURNAMENT.to_dict())


@eel.expose
def tournament_start_match(match_id: str) -> str:
    """
    Start a specific match in the tournament. Launches the match automatically.
    
    Args:
        match_id: ID of the match to start
    
    Returns:
        JSON string with match info and status
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    # Find the match
    match = None
    for m in CURRENT_TOURNAMENT.matches:
        if m.match_id == match_id:
            match = m
            break
    
    # Also check losers bracket for double elimination
    if match is None:
        for m in CURRENT_TOURNAMENT.losers_bracket_matches:
            if m.match_id == match_id:
                match = m
                break
    
    if match is None:
        return json.dumps({'error': f'Match {match_id} not found'})
    
    if match.completed:
        return json.dumps({'error': f'Match {match_id} already completed'})
    
    # For team-based matches, check teams; otherwise check participants
    if match.team1 is not None and match.team2 is not None:
        pass  # team-based match, handled by build_match_bot_list
    elif match.participant1 is None or match.participant2 is None:
        return json.dumps({'error': f'Match {match_id} has no participants'})
    
    # Build bot list for match runner (handles both 1v1 and team-based matches)
    bot_list = build_match_bot_list(match)
    
    # Build match settings, applying the tournament's custom mutators
    # (stored in CURRENT_TOURNAMENT.match_settings) with sensible defaults
    # for any mutator the user did not explicitly set.
    default_mutators = {
        'match_length': '5 Minutes',
        'max_score': '5 Goals',
        'overtime': 'Unlimited',
        'series_length': 'Unlimited',
        'game_speed': 'Default',
        'ball_max_speed': 'Default',
        'ball_type': 'Default',
        'ball_weight': 'Default',
        'ball_size': 'Default',
        'ball_bounciness': 'Default',
        'boost_amount': 'Default',
        'rumble': 'None',
        'boost_strength': '1x',
        'gravity': 'Default',
        'demolish': 'Default',
        'respawn_time': '3 Seconds'
    }

    # CURRENT_TOURNAMENT.match_settings is a flat {mutator_key: value} map
    # (the frontend sends JSON.stringify(newTournament.mutators)).
    custom_mutators = CURRENT_TOURNAMENT.match_settings or {}
    if not isinstance(custom_mutators, dict):
        custom_mutators = {}

    mutators = dict(default_mutators)
    for key, value in custom_mutators.items():
        if key in default_mutators and value:
            mutators[key] = value

    match_settings = {
        'game_mode': 'Soccer',
        'map': 'DFHStadium',
        'skip_replays': True,
        'instant_start': False,
        'enable_lockstep': False,
        'enable_rendering': True,
        'enable_state_setting': False,
        'auto_save_replay': False,
        'match_behavior': 'Restart',
        'mutators': mutators,
        'scripts': []
    }
    
    # Launch the match in a separate thread
    eel.spawn(launch_tournament_match, bot_list, match_settings, match_id)
    
    return json.dumps({
        'success': True,
        'match_id': match_id,
        'participants': [match.participant1.name, match.participant2.name]
    })


def launch_tournament_match(bot_list: list, match_settings: dict, match_id: str):
    """
    Launch the tournament match in a separate thread.
    """
    from rlbot_gui.match_runner.match_runner import start_match_helper
    from rlbot_gui.persistence.settings import load_settings, load_launcher_settings, launcher_preferences_from_map
    
    print(f"DEBUG: launch_tournament_match called with match_id={match_id}")
    print(f"DEBUG: bot_list={bot_list}")
    print(f"DEBUG: match_settings={match_settings}")
    
    try:
        launcher_preference_map = load_launcher_settings()
        launcher_prefs = launcher_preferences_from_map(launcher_preference_map)
        print(f"DEBUG: About to call start_match_helper")
        team_scores = start_match_helper(bot_list, match_settings, launcher_prefs)
        print(f"DEBUG: start_match_helper returned team_scores={team_scores}")
        
        # Automatically record the winner based on team scores
        if team_scores:
            # Find which team won (higher score)
            team_scores_sorted = sorted(team_scores, key=lambda x: x['score'], reverse=True)
            winning_team_index = team_scores_sorted[0]['team_index']
            winning_score = team_scores_sorted[0]['score']
            losing_score = team_scores_sorted[1]['score'] if len(team_scores_sorted) > 1 else 0
            
            # Create score array ordered by team_index (participant1=team0, participant2=team1)
            score_by_team = {ts['team_index']: ts['score'] for ts in team_scores}
            ordered_scores = [score_by_team.get(0, 0), score_by_team.get(1, 0)]
            
            # Find the winner's name.
            # For team-based matches the bracket stand-in participant is named
            # after the team, so we must use the team name (not a bot name).
            winner_name = None
            match = None
            if CURRENT_TOURNAMENT is not None:
                for m in CURRENT_TOURNAMENT.matches:
                    if m.match_id == match_id:
                        match = m
                        break
                if match is None:
                    for m in CURRENT_TOURNAMENT.losers_bracket_matches:
                        if m.match_id == match_id:
                            match = m
                            break

            if match is not None and match.team1 is not None and match.team2 is not None:
                winner_name = match.team1.name if winning_team_index == 0 else match.team2.name
            else:
                for bot in bot_list:
                    if bot['team'] == winning_team_index:
                        winner_name = bot['name']
                        break
            
            if winner_name:
                print(f"DEBUG: Auto-recording winner: {winner_name} with score {winning_score}")
                # Call tournament_record_result to advance the tournament
                result = tournament_record_result(match_id, winner_name, json.dumps(ordered_scores))
                print(f"DEBUG: tournament_record_result returned: {result}")
            else:
                print(f"DEBUG: Could not find winner for team {winning_team_index}")
        else:
            print(f"DEBUG: No team scores returned, match may have been interrupted")
    except Exception as e:
        print(f"Error launching tournament match: {e}")
        import traceback
        traceback.print_exc()


@eel.expose
def tournament_match_started(match_id: str) -> None:
    """
    Called when a match is started. This is a placeholder for future functionality.
    
    Args:
        match_id: ID of the match that was started
    """
    # Currently just a placeholder - can be used for tracking match state later
    pass


@eel.expose
def tournament_record_result(match_id: str, winner_name: str, score_json: str) -> str:
    """
    Record the result of a match and advance the winner.
    
    Args:
        match_id: ID of the match
        winner_name: Name of the winning participant
        score_json: JSON string of score tuple
    
    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    score = tuple(json.loads(score_json))
    
    # Find the match
    match = None
    for m in CURRENT_TOURNAMENT.matches:
        if m.match_id == match_id:
            match = m
            break
    
    # Also check losers bracket
    if match is None:
        for m in CURRENT_TOURNAMENT.losers_bracket_matches:
            if m.match_id == match_id:
                match = m
                break
    
    if match is None:
        return json.dumps({'error': f'Match {match_id} not found'})
    
    # Find the winner participant
    winner = None
    if match.participant1 and match.participant1.name == winner_name:
        winner = match.participant1
    elif match.participant2 and match.participant2.name == winner_name:
        winner = match.participant2
    
    if winner is None:
        return json.dumps({'error': f'Winner {winner_name} not found in match'})
    
    print(f"DEBUG: tournament_record_result({match_id}, {winner_name}, {score})")
    print(f"DEBUG: Match {match_id} round={match.round_num}, next_match_id={match.next_match_id}")
    
    # Record result
    match.winner = winner
    match.score = score
    match.completed = True

    # For team-based matches, record the winning team and update W/L
    winning_team = None
    losing_team = None
    if CURRENT_TOURNAMENT.teams:
        for t in CURRENT_TOURNAMENT.teams:
            if t.team_id == winner.participant_id:
                winning_team = t
                break
        if winning_team is not None:
            match.winner_team = winning_team
            winning_team.wins += 1
            # Find the losing team
            if match.team1 is not None and match.team2 is not None:
                losing_team = match.team2 if match.team1.team_id == winning_team.team_id else match.team1
                if losing_team is not None:
                    losing_team.losses += 1

    # Check for tournament completion
    if is_tournament_final_match(match):
        print(f"DEBUG: Match {match_id} is the final match, tournament complete!")
        CURRENT_TOURNAMENT.winner = winner
        if winning_team is not None:
            CURRENT_TOURNAMENT.winner_team = winning_team
        CURRENT_TOURNAMENT.completed = True
    else:
        print(f"DEBUG: Match {match_id} is not final, advancing {winner_name}")
        # Advance winner to next match
        advance_winner(match, winner)
    
    # Save state
    return tournament_save_state()


def is_tournament_final_match(match: Match) -> bool:
    """
    Check if this is the final match of the tournament.
    
    A match is the final if the winner doesn't advance to another match
    (i.e., next_match_id is None).
    """
    # If the match has no next match, it's the final
    is_final = match.next_match_id is None
    print(f"DEBUG: is_tournament_final_match({match.match_id}) = {is_final} (next_match_id={match.next_match_id})")
    return is_final


def advance_winner(match: Match, winner: Participant) -> None:
    """
    Advance the winner to their next match.
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return
    
    next_match_id = match.next_match_id
    if next_match_id is None:
        print(f"DEBUG: advance_winner({match.match_id}) - no next match, winner {winner.name} is tournament champion")
        return
    
    print(f"DEBUG: advance_winner({match.match_id}) - advancing {winner.name} to match {next_match_id}")
    
    # Find next match
    next_match = None
    for m in CURRENT_TOURNAMENT.matches:
        if m.match_id == next_match_id:
            next_match = m
            break
    
    # Check losers bracket for double elimination
    if next_match is None:
        for m in CURRENT_TOURNAMENT.losers_bracket_matches:
            if m.match_id == next_match_id:
                next_match = m
                break
    
    if next_match is None:
        print(f"DEBUG: advance_winner({match.match_id}) - could not find next match {next_match_id}")
        return
    
    # Assign winner to next match
    if next_match.participant1 is None:
        next_match.participant1 = winner
    elif next_match.participant2 is None:
        next_match.participant2 = winner
    else:
        print(f"DEBUG: advance_winner({match.match_id}) - next match {next_match_id} already has both participants")
        return

    # For team-based matches, attach the winning team to the next match
    if CURRENT_TOURNAMENT.teams:
        winning_team = None
        for t in CURRENT_TOURNAMENT.teams:
            if t.team_id == winner.participant_id:
                winning_team = t
                break
        if winning_team is not None:
            if next_match.participant1 is winner and next_match.team1 is None:
                next_match.team1 = winning_team
            elif next_match.participant2 is winner and next_match.team2 is None:
                next_match.team2 = winning_team
    
    print(f"DEBUG: advance_winner({match.match_id}) - {winner.name} assigned to {next_match_id} (slot {'participant1' if next_match.participant1 == winner else 'participant2'})")
    
    # Only auto-complete as a bye if this is round 1 (power of 2 bracket with odd participants)
    # In later rounds, a match with 1 participant just means waiting for the other winner
    if next_match.round_num == 1 and next_match.participant1 is not None and next_match.participant2 is None:
        # Only one participant in round 1 - they get a bye
        print(f"DEBUG: advance_winner({match.match_id}) - M1 bye for {winner.name}")
        next_match.completed = True
        next_match.winner = next_match.participant1
        advance_winner(next_match, next_match.participant1)


@eel.expose
def tournament_add_participant(participant_json: str) -> str:
    """
    Add a participant to the current tournament.
    
    Args:
        participant_json: JSON string of participant data
    
    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    participant_data = json.loads(participant_json)
    participant = Participant.from_dict(participant_data)
    
    # Generate unique ID if not provided
    if not participant.participant_id:
        participant.participant_id = str(uuid.uuid4())[:8]
    
    CURRENT_TOURNAMENT.participants.append(participant)
    
    return tournament_save_state()


@eel.expose
def tournament_remove_participant(participant_id: str) -> str:
    """
    Remove a participant from the current tournament.
    
    Args:
        participant_id: ID of participant to remove
    
    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    CURRENT_TOURNAMENT.participants = [
        p for p in CURRENT_TOURNAMENT.participants 
        if p.participant_id != participant_id
    ]
    
    return tournament_save_state()


@eel.expose
def tournament_randomize_seeding() -> str:
    """
    Randomize the seeding of participants.
    
    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    import random
    
    # Shuffle participants and reassign seeds
    shuffled = CURRENT_TOURNAMENT.participants.copy()
    random.shuffle(shuffled)
    
    for i, p in enumerate(shuffled):
        p.seed = i
    
    CURRENT_TOURNAMENT.participants = shuffled

    # Regenerate bracket
    if CURRENT_TOURNAMENT.team_size > 1:
        # Re-form teams randomly and regenerate the team bracket
        teams = form_teams_random(shuffled, CURRENT_TOURNAMENT.team_size)
        CURRENT_TOURNAMENT.teams = teams
        matches, losers_matches = generate_team_bracket(teams, CURRENT_TOURNAMENT.format)
        CURRENT_TOURNAMENT.matches = matches
        CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
    elif CURRENT_TOURNAMENT.format == 'single_elimination':
        matches, num_rounds = generate_single_elimination_bracket(shuffled)
        CURRENT_TOURNAMENT.matches = matches
    elif CURRENT_TOURNAMENT.format == 'double_elimination':
        winners_matches, losers_matches, num_rounds = generate_double_elimination_bracket(shuffled)
        CURRENT_TOURNAMENT.matches = winners_matches
        CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
    elif CURRENT_TOURNAMENT.format == 'round_robin':
        matches = generate_round_robin_bracket(shuffled)
        CURRENT_TOURNAMENT.matches = matches

    return tournament_save_state()


TOURNAMENTS_LIST_KEY = "tournaments_list"


@eel.expose
def tournament_save_to_list() -> str:
    """
    Save current tournament to the saved tournaments list.
    
    Returns:
        JSON string of tournament state
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    settings = QSettings("rlbotgui", "tournament_save")
    
    # Get existing list
    list_json = settings.value(TOURNAMENTS_LIST_KEY, type=str)
    tournaments_list = json.loads(list_json) if list_json else []
    
    # Create tournament metadata
    serialized = CURRENT_TOURNAMENT.to_dict()
    tournament_meta = {
        'tournament_id': CURRENT_TOURNAMENT.tournament_id,
        'name': CURRENT_TOURNAMENT.name,
        'format': CURRENT_TOURNAMENT.format,
        'participants': [p.to_dict() for p in CURRENT_TOURNAMENT.participants],
        'completed': CURRENT_TOURNAMENT.completed,
        'save_data': json.dumps(serialized)
    }
    
    # Check if tournament already exists in list
    existing_index = None
    for i, t in enumerate(tournaments_list):
        if t['tournament_id'] == CURRENT_TOURNAMENT.tournament_id:
            existing_index = i
            break
    
    if existing_index is not None:
        tournaments_list[existing_index] = tournament_meta
    else:
        tournaments_list.append(tournament_meta)
    
    # Save updated list
    settings.setValue(TOURNAMENTS_LIST_KEY, json.dumps(tournaments_list))
    
    return json.dumps(serialized)


@eel.expose
def tournament_get_saved_list() -> str:
    """
    Get list of saved tournaments.
    
    Returns:
        JSON string of tournaments list
    """
    settings = QSettings("rlbotgui", "tournament_save")
    list_json = settings.value(TOURNAMENTS_LIST_KEY, type=str)
    return list_json if list_json else "[]"


@eel.expose
def tournament_delete_from_list(tournament_id: str) -> str:
    """
    Delete a tournament from the saved list.
    
    Args:
        tournament_id: ID of tournament to delete
    
    Returns:
        Success message
    """
    settings = QSettings("rlbotgui", "tournament_save")
    list_json = settings.value(TOURNAMENTS_LIST_KEY, type=str)
    tournaments_list = json.loads(list_json) if list_json else []
    
    # Remove tournament from list
    tournaments_list = [t for t in tournaments_list if t['tournament_id'] != tournament_id]
    
    # Save updated list
    settings.setValue(TOURNAMENTS_LIST_KEY, json.dumps(tournaments_list))
    
    return json.dumps({'success': True})


@eel.expose
def tournament_load_from_id(tournament_id: str) -> str:
    """
    Load a tournament from the saved list by ID.
    
    Args:
        tournament_id: ID of tournament to load
    
    Returns:
        JSON string of tournament state
    """
    global CURRENT_TOURNAMENT
    
    settings = QSettings("rlbotgui", "tournament_save")
    list_json = settings.value(TOURNAMENTS_LIST_KEY, type=str)
    tournaments_list = json.loads(list_json) if list_json else []
    
    # Find tournament
    for t in tournaments_list:
        if t['tournament_id'] == tournament_id:
            CURRENT_TOURNAMENT = TournamentState.from_dict(json.loads(t['save_data']))
            return json.dumps(CURRENT_TOURNAMENT.to_dict())
    
    return json.dumps({'error': f'Tournament {tournament_id} not found'})


@eel.expose
def tournament_export_to_json() -> str:
    """
    Export the current tournament to a JSON string for file export.
    
    Returns:
        JSON string of complete tournament state (suitable for saving to file)
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    # Return the full serialized state
    return json.dumps(CURRENT_TOURNAMENT.to_dict(), indent=2)


@eel.expose
def tournament_import_from_json(tournament_json: str) -> str:
    """
    Import a tournament from a JSON string.
    
    Args:
        tournament_json: JSON string of tournament state
    
    Returns:
        JSON string of loaded tournament state
    """
    global CURRENT_TOURNAMENT
    
    try:
        data = json.loads(tournament_json)
        CURRENT_TOURNAMENT = TournamentState.from_dict(data)
        return tournament_save_state()
    except Exception as e:
        return json.dumps({'error': f'Failed to import tournament: {str(e)}'})


@eel.expose
def tournament_save_file_dialog(file_content: str, default_filename: str = 'tournament.json') -> str:
    """
    Open a native "Save As" file dialog and write the given content to the
    chosen location.

    Eel 0.18.2 does not ship eel.savefile(), so we delegate the file dialog
    to PyQt5 (already a project dependency). This mirrors the existing
    pick_location() pattern in gui.py.

    Args:
        file_content: String content to write (the tournament JSON)
        default_filename: Suggested filename shown in the dialog

    Returns:
        JSON string:
            {'success': True,  'path': ...}  on success
            {'cancelled': True}              if the user closed the dialog
            {'error': ...}                   on failure
    """
    from PyQt5.QtWidgets import QApplication, QFileDialog
    import sys

    # QApplication must exist before any Q* widget/dialog is used.
    # Reuse the existing instance if one is already running.
    app = QApplication.instance() or QApplication(sys.argv)

    file_path, _ = QFileDialog.getSaveFileName(
        None,
        "Save Tournament",
        default_filename,
        "JSON Files (*.json);;All Files (*)"
    )

    if not file_path:
        # User cancelled the dialog
        return json.dumps({'cancelled': True})

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return json.dumps({'success': True, 'path': file_path})
    except Exception as e:
        return json.dumps({'error': f'Failed to write file: {str(e)}'})
