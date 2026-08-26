"""
Manages tournament state and execution
"""
import json
import uuid
from typing import List, Dict, Any, Optional

import eel
from PyQt5.QtCore import QSettings

from rlbot_gui.tournament.tournament_state import TournamentState, Participant, Match
from rlbot_gui.tournament.bracket_generator import (
    generate_single_elimination_bracket,
    generate_double_elimination_bracket,
    generate_round_robin_bracket
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
def tournament_new(name: str, tournament_format: str, participants_json: str) -> str:
    """
    Create a new tournament.
    
    Args:
        name: Tournament name
        tournament_format: 'single_elimination', 'double_elimination', or 'round_robin'
        participants_json: JSON string of participant list
    
    Returns:
        JSON string of tournament state
    """
    global CURRENT_TOURNAMENT
    
    participants_data = json.loads(participants_json)
    participants = [Participant.from_dict(p) for p in participants_data]
    
    tournament_id = str(uuid.uuid4())[:8]
    
    CURRENT_TOURNAMENT = TournamentState(
        name=name,
        tournament_id=tournament_id,
        format=tournament_format,
        participants=participants
    )
    
    # Generate bracket based on format
    if tournament_format == 'single_elimination':
        matches, num_rounds = generate_single_elimination_bracket(participants)
        CURRENT_TOURNAMENT.matches = matches
        CURRENT_TOURNAMENT.current_round = 1
    elif tournament_format == 'double_elimination':
        winners_matches, losers_matches, num_rounds = generate_double_elimination_bracket(participants)
        CURRENT_TOURNAMENT.matches = winners_matches
        CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
        CURRENT_TOURNAMENT.current_round = 1
    elif tournament_format == 'round_robin':
        matches = generate_round_robin_bracket(participants)
        CURRENT_TOURNAMENT.matches = matches
        CURRENT_TOURNAMENT.current_round = 1
    
    return tournament_save_state()


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
def tournament_start_match(match_id: str) -> Optional[str]:
    """
    Start a specific match in the tournament.
    
    Args:
        match_id: ID of the match to start
    
    Returns:
        JSON string of match configuration or None
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
    
    if match.participant1 is None or match.participant2 is None:
        return json.dumps({'error': f'Match {match_id} has no participants'})
    
    # Generate match configuration
    config = generate_match_config_from_match(match, CURRENT_TOURNAMENT.format)
    config['match_id'] = match_id
    
    return json.dumps(config)


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
    
    # Record result
    match.winner = winner
    match.score = score
    match.completed = True
    
    # Check for tournament completion
    if is_tournament_final_match(match):
        CURRENT_TOURNAMENT.winner = winner
        CURRENT_TOURNAMENT.completed = True
    else:
        # Advance winner to next match
        advance_winner(match, winner)
    
    # Save state
    return tournament_save_state()


def is_tournament_final_match(match: Match) -> bool:
    """
    Check if this is the final match of the tournament.
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return False
    
    # For single elimination, check if this is the last match
    remaining = [m for m in CURRENT_TOURNAMENT.matches if not m.completed]
    
    # Filter out matches that don't have participants yet (future rounds)
    active_remaining = [m for m in remaining if m.participant1 is not None and m.participant2 is not None]
    
    return len(active_remaining) <= 1


def advance_winner(match: Match, winner: Participant) -> None:
    """
    Advance the winner to their next match.
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return
    
    next_match_id = match.next_match_id
    if next_match_id is None:
        return
    
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
        return
    
    # Assign winner to next match
    if next_match.participant1 is None:
        next_match.participant1 = winner
    elif next_match.participant2 is None:
        next_match.participant2 = winner
    
    # If both participants are ready, check if match can auto-start (byes)
    if next_match.participant1 is not None and next_match.participant2 is None:
        # Only one participant - they get a bye
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
    if CURRENT_TOURNAMENT.format == 'single_elimination':
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
def tournament_match_started(match_id: str) -> None:
    """
    Called when a match is started. This is a placeholder for future functionality.
    
    Args:
        match_id: ID of the match that was started
    """
    # Currently just a placeholder - can be used for tracking match state later
    pass
