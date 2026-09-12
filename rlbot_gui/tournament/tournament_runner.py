"""
Manages tournament state and execution
"""
import json
import random
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

import eel
from PyQt5.QtCore import QSettings

from rlbot_gui.tournament.tournament_state import TournamentState, Participant, Match, Team
from rlbot_gui.tournament.bracket_generator import (
    generate_single_elimination_bracket,
    generate_double_elimination_bracket,
    generate_round_robin_bracket,
    calculate_swiss_rounds,
    generate_swiss_round1,
    generate_swiss_next_round,
    calculate_swiss_standings,
    determine_swiss_winner,
    rank_entities
)
from rlbot_gui.tournament.team_manager import (
    validate_team_formation,
    form_teams_random,
    form_teams_seeded,
    form_teams_manual,
    generate_team_bracket,
    build_match_bot_list,
    team_balance_report,
    generate_team_names,
    assign_random_team_names
)
from rlbot_gui.persistence.settings import load_settings, MATCH_SETTINGS_KEY, load_launcher_settings, launcher_preferences_from_map

# Global state for current tournament
CURRENT_TOURNAMENT: Optional[TournamentState] = None

# Map pools per game mode, used when a tournament has map randomization enabled.
# Each pool maps a map name to its selection weight. Weights mirror Rocket League's
# official map rotation drop chances (normalized to the subset of rotation maps
# RLBot can actually load). Maps that exist in RLBot but are outside a mode's
# official rotation are included as extra rare (weight 1.0); special themed
# variants are super rare (weight 0.25).
#
# Note: several rotation maps cannot be offered because RLBot cannot load them
# (Futura Garden, Boostfield Mall, Parc de Paris, Drift Woods, NeoTokyo Arcade,
# 10th Anniversary, Salty Fest, Salty Shallows, Quads and Knockout arenas).

# Base soccar pool: rotation maps at their real drop chances.
SOCCAR_ROTATION_WEIGHTS: Dict[str, float] = {
    'DFHStadium': 7.67,
    'Mannfield': 7.67,
    'BeckwithPark': 4.93,
    'ChampionsField': 4.56,
    'UtopiaColiseum': 4.38,
    'UrbanCentral': 4.01,
    'Farmstead_Pitched': 3.65,
    'ForbiddenTemple': 3.65,
    'NeoTokyo': 3.65,
    'Wasteland_Pitched': 3.65,
    'EstadioVida_Dusk': 2.92,
    'SovereignHeights': 2.74,
    'AquaDome': 2.74,
    'DeadeyeCanyon_Oasis': 2.55,
    'ChampionsField_Day': 2.37,
    'ForbiddenTemple_Day': 2.37,
    'BeckwithPark_Midnight': 1.46,
    'UtopiaColiseum_Gilded': 1.27,
    'Mannfield_Dusk': 1.09,
    'DFHStadium_Day': 1.02,
    'UrbanCentral_Dawn': 0.91,
    'UrbanCentral_Night': 0.91,
    'BeckwithPark_Stormy': 0.73,
    'Mannfield_Night': 0.73,
    'DFHStadium_Stormy': 0.58,
    'UtopiaColiseum_Dusk': 0.54,
    'Mannfield_Stormy': 0.36,
}

# Extra rare: plain soccar maps that are outside the current rotation.
SOCCAR_EXTRA_RARE_WEIGHTS: Dict[str, float] = {
    'StarbaseArc': 1.0,
    'SaltyShores': 1.0,
    'SaltyShores_Night': 1.0,
    'Wasteland': 1.0,
    'Farmstead_Night': 1.0,
    'DeadeyeCanyon': 1.0,
}

# Super rare: special themed variants of soccar arenas.
SOCCAR_SUPER_RARE_WEIGHTS: Dict[str, float] = {
    'StarbaseArc_Aftermath': 0.25,
    'DFHStadium_Circuit': 0.25,
    'NeonFields': 0.25,
    'RivalsArena': 0.25,
    'BeckwithPark_GothamNight': 0.25,
    'Farmstead_Spooky': 0.25,
    'Farmstead_Upsidedown': 0.25,
    'NeoTokyo_Comic': 0.25,
    'Neotokyo_Hacked': 0.25,
    'ForbiddenTemple_FireAndIce': 0.25,
    'ChampionsField_NikeFC': 0.25,
    'UrbanCentral_Haunted': 0.25,
}

SOCCAR_MAP_POOL: Dict[str, float] = {
    **SOCCAR_ROTATION_WEIGHTS,
    **SOCCAR_EXTRA_RARE_WEIGHTS,
    **SOCCAR_SUPER_RARE_WEIGHTS,
}

# Rumble pool: rumble rotation drop chances (available maps only).
RUMBLE_MAP_POOL: Dict[str, float] = {
    'DFHStadium': 6.1,
    'Mannfield': 6.1,
    'BeckwithPark': 3.92,
    'ChampionsField': 3.63,
    'UtopiaColiseum': 3.49,
    'UrbanCentral': 3.2,
    'Arctagon': 2.9,
    'Badlands': 2.9,
    'Badlands_Night': 2.9,
    'DoubleGoal': 2.9,
    'Farmstead_Pitched': 2.9,
    'ForbiddenTemple': 2.9,
    'NeoTokyo': 2.9,
    'ThrowbackStadium': 2.9,
    'TokyoUnderpass': 2.9,
    'Underpass': 2.9,
    'Wasteland_Pitched': 2.9,
    'AquaDome': 4.5,
    'EstadioVida_Dusk': 2.32,
    'SovereignHeights': 2.18,
    'DeadeyeCanyon_Oasis': 2.03,
    'ChampionsField_Day': 1.89,
    'ForbiddenTemple_Day': 1.89,
    'BeckwithPark_Midnight': 1.16,
    'UtopiaColiseum_Gilded': 1.01,
    'Mannfield_Dusk': 0.87,
    'DFHStadium_Day': 0.81,
    'UrbanCentral_Dawn': 0.72,
    'UrbanCentral_Night': 0.72,
    'BeckwithPark_Stormy': 0.58,
    'Mannfield_Night': 0.58,
    'DFHStadium_Stormy': 0.46,
    'UtopiaColiseum_Dusk': 0.43,
    'Mannfield_Stormy': 0.29,
    **SOCCAR_EXTRA_RARE_WEIGHTS,
    **SOCCAR_SUPER_RARE_WEIGHTS,
}

# Heatseeker pool: soccar maps plus the special LTM arenas (Up To No Good,
# Haunted Heatseeker, Heatseeker Ricochet, Spike Drop, Rocket Labs) as super rare.
HEATSEEKER_MAP_POOL: Dict[str, float] = {
    **SOCCAR_MAP_POOL,
    'Basin': 0.25,
    'Corridor': 0.25,
    'Galleon': 0.25,
    'GalleonRetro': 0.25,
    'Loophole': 0.25,
    'Hourglass': 0.25,
    'Barricade': 0.25,
    'Colossus': 0.25,
    'Octagon': 0.25,
    'Pillars': 0.25,
    'Cosmic': 0.25,
    'UtopiaRetro': 0.25,
}

# Hockey pool: Snow Day rotation maps at their real chances; the other snowy
# variants (not in the Snow Day rotation) are extra rare.
HOCKEY_MAP_POOL: Dict[str, float] = {
    'DFHStadium_Snowy': 33.33,
    'Mannfield_Snowy': 33.33,
    'UtopiaColiseum_Snowy': 33.33,
    'ThrowbackStadium_Snowy': 1.0,
    'BeckwithPark_Snowy': 1.0,
}

MAP_POOLS: Dict[str, Dict[str, float]] = {
    'Soccer': SOCCAR_MAP_POOL,
    'Rumble': RUMBLE_MAP_POOL,
    'Heatseeker': HEATSEEKER_MAP_POOL,
    'Hoops': {'Hoops_DunkHouse': 50.0, 'Hoops_TheBlock': 50.0},
    'Dropshot': {'DropShot_Core707': 100.0},
    'Hockey': HOCKEY_MAP_POOL,
    'Gridiron': {'ChampionsField_NFL': 100.0},
}


def pick_random_map(game_mode: str) -> str:
    """
    Weighted-random map selection for a game mode.

    Picks from the mode's pool using each map's rotation weight, so common
    rotation maps show up often and special variants stay rare.
    """
    pool = MAP_POOLS.get(game_mode) or SOCCAR_MAP_POOL
    maps = list(pool.keys())
    weights = list(pool.values())
    return random.choices(maps, weights=weights, k=1)[0]


def match_has_humans(match: Match) -> bool:
    """
    Check if a match contains one or more human participants.

    Used by the LAN Match Workflow (Phase 3): matches with humans should
    use the staging -> Players Ready -> real match flow so the host can set
    up the LAN host and let humans join before bots are injected.
    """
    def _has_human(p) -> bool:
        return p is not None and p.participant_type == 'human'

    if match.team1 is not None and match.team2 is not None:
        return (any(_has_human(p) for p in match.team1.participants) or
                any(_has_human(p) for p in match.team2.participants))
    return _has_human(match.participant1) or _has_human(match.participant2)


def count_humans_in_match(match: Match) -> int:
    """Count the number of human participants in a match."""
    def _count(p) -> int:
        return 1 if (p is not None and p.participant_type == 'human') else 0

    if match.team1 is not None and match.team2 is not None:
        return (sum(_count(p) for p in match.team1.participants) +
                sum(_count(p) for p in match.team2.participants))
    return _count(match.participant1) + _count(match.participant2)


@eel.expose
def tournament_new(name: str, tournament_format: str, participants_json: str, match_settings_json: str = '{}', team_size: int = 1, allow_duplicates: bool = False, swiss_rounds: int = 0, map: str = '', game_mode: str = 'Soccer', scripts_json: str = '[]', randomize_map: bool = False, mercy_rule: int = 0) -> str:
    """
    Create a new tournament.
    
    Args:
        name: Tournament name
        tournament_format: 'single_elimination', 'double_elimination', 'round_robin', or 'swiss'
        participants_json: JSON string of participant list
        match_settings_json: JSON string of match settings (optional)
        team_size: Participants per team (1, 2, 3, 4, or 5). Default 1 (1v1).
        allow_duplicates: When True, each team member is a copy of one participant.
        swiss_rounds: Optional override for the number of Swiss rounds.
            0 (default) = auto-calculate as ceil(log2(participants)).
        map: Optional map ID (e.g., 'DFHStadium', 'BeckwithPark'). Stored with tournament state
            and displayed in the Human Match Info modal.
        game_mode: Game mode for all matches (e.g. 'Soccer', 'Hoops', 'Dropshot',
            'Hockey', 'Rumble', 'Heatseeker', 'Gridiron').
        scripts_json: JSON list of custom script configs to load into every match
            (e.g. [{'name': 'Knockout', 'path': 'C:/.../blueprint.cfg'}]).
        randomize_map: When True, each match picks a random map from the pool
            for the tournament's game mode instead of using the fixed map.
        mercy_rule: Goal differential that ends a match early (0 = disabled).
            When one team leads by this many goals, the match ends immediately
            and the score/stats up to that point are kept.
    
    Returns:
        JSON string of tournament state
    """
    global CURRENT_TOURNAMENT
    
    participants_data = json.loads(participants_json)
    participants = [Participant.from_dict(p) for p in participants_data]
    
    # Parse match settings
    match_settings = json.loads(match_settings_json) if match_settings_json else {}

    # Parse custom scripts
    try:
        scripts = json.loads(scripts_json) if scripts_json else []
    except (json.JSONDecodeError, TypeError):
        scripts = []
    
    # Validate team size
    if team_size not in (1, 2, 3, 4, 5):
        return json.dumps({'error': f'Team size must be 1, 2, 3, 4, or 5 (got {team_size})'})
    
    # Validate participant count for team formation
    if team_size > 1:
        valid, error_msg = validate_team_formation(len(participants), team_size, allow_duplicates)
        if not valid:
            return json.dumps({'error': error_msg})
    
    # Validate Swiss format requirements
    if tournament_format == 'swiss':
        num_entities = len(participants) // team_size if team_size > 1 else len(participants)
        if num_entities < 2:
            return json.dumps({'error': 'Swiss format requires at least 2 participants (or 2 teams)'})
        if num_entities % 2 != 0:
            return json.dumps({'error': f'Swiss format requires an even number of participants/teams (got {num_entities})'})
    
    tournament_id = str(uuid.uuid4())[:8]
    
    # Determine selected map (empty string → None)
    selected_map = map if map and map.strip() else None

    # Calculate Swiss rounds
    if tournament_format == 'swiss':
        num_entities = len(participants) // team_size if team_size > 1 else len(participants)
        if swiss_rounds and swiss_rounds > 0:
            calculated_rounds = swiss_rounds
        else:
            calculated_rounds = calculate_swiss_rounds(num_entities)
    else:
        calculated_rounds = 0
    
    # Validate game mode
    valid_game_modes = ('Soccer', 'Hoops', 'Dropshot', 'Hockey', 'Rumble', 'Heatseeker', 'Gridiron')
    if game_mode not in valid_game_modes:
        game_mode = 'Soccer'

    CURRENT_TOURNAMENT = TournamentState(
        name=name,
        tournament_id=tournament_id,
        format=tournament_format,
        participants=participants,
        match_settings=match_settings,
        team_size=team_size,
        allow_duplicates=allow_duplicates,
        swiss_rounds=calculated_rounds,
        map=selected_map,
        game_mode=game_mode,
        scripts=scripts,
        randomize_map=randomize_map,
        mercy_rule=max(0, int(mercy_rule or 0))
    )
    
    if team_size > 1:
        # Form teams (random assignment by default) and generate team bracket
        teams = form_teams_random(participants, team_size, allow_duplicates=allow_duplicates)
        CURRENT_TOURNAMENT.teams = teams
        matches, losers_matches, grand_final_match = generate_team_bracket(teams, tournament_format)
        CURRENT_TOURNAMENT.matches = matches
        CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
        if grand_final_match:
            CURRENT_TOURNAMENT.matches.append(grand_final_match)
    else:
        # 1v1: existing participant-based bracket
        if tournament_format == 'single_elimination':
            matches, num_rounds = generate_single_elimination_bracket(participants)
            CURRENT_TOURNAMENT.matches = matches
        elif tournament_format == 'double_elimination':
            winners_matches, losers_matches, grand_final_match, num_rounds = generate_double_elimination_bracket(participants)
            CURRENT_TOURNAMENT.matches = winners_matches
            CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
            if grand_final_match:
                CURRENT_TOURNAMENT.matches.append(grand_final_match)
        elif tournament_format == 'round_robin':
            matches = generate_round_robin_bracket(participants)
            CURRENT_TOURNAMENT.matches = matches
        elif tournament_format == 'swiss':
            matches = generate_swiss_round1(participants)
            CURRENT_TOURNAMENT.matches = matches
    
    CURRENT_TOURNAMENT.current_round = 1
    # Add to saved tournaments list
    tournament_save_to_list()
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
    allow_duplicates = CURRENT_TOURNAMENT.allow_duplicates
    valid, error_msg = validate_team_formation(len(participants), team_size, allow_duplicates)
    if not valid:
        return json.dumps({'error': error_msg})

    if assignment_method == 'seeded':
        teams = form_teams_seeded(participants, team_size, allow_duplicates=allow_duplicates)
    elif assignment_method == 'manual':
        # Manual assignment is done client-side via tournament_set_team_members
        return json.dumps({'error': 'Use tournament_set_team_members for manual assignment'})
    else:
        teams = form_teams_random(participants, team_size, allow_duplicates=allow_duplicates)

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
    matches, losers_matches, grand_final_match = generate_team_bracket(teams, CURRENT_TOURNAMENT.format)
    CURRENT_TOURNAMENT.matches = matches
    CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
    if grand_final_match:
        CURRENT_TOURNAMENT.matches.append(grand_final_match)
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
def tournament_reorder_team_member(team_index: int, from_slot: int, to_slot: int) -> str:
    """
    Reorder a member within a team (slot assignment).

    The order of team.participants determines the in-game slot: index 0 is
    slot 0, index 1 is slot 1, etc. (see build_match_bot_list). This lets
    operators designate which human fills which seat.

    Args:
        team_index: 0-based index of the team
        from_slot: Current index of the member to move
        to_slot: Target index for the member

    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    if team_index < 0 or team_index >= len(CURRENT_TOURNAMENT.teams):
        return json.dumps({'error': f'Team index {team_index} out of range'})

    team = CURRENT_TOURNAMENT.teams[team_index]
    n = len(team.participants)
    if from_slot < 0 or from_slot >= n or to_slot < 0 or to_slot >= n:
        return json.dumps({'error': f'Slot index out of range (team has {n} members)'})

    member = team.participants.pop(from_slot)
    team.participants.insert(to_slot, member)

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
def tournament_randomize_team_names() -> str:
    """
    Re-randomize all team names with unique values from the name pool.

    This generates fresh random names for all teams, ensuring no duplicates
    within the tournament. Existing names are excluded from the pool to
    prevent collisions.

    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    if not CURRENT_TOURNAMENT.teams:
        return json.dumps({'error': 'No teams to randomize'})

    try:
        assign_random_team_names(CURRENT_TOURNAMENT.teams)
        # Update stand-in participant names in matches so bracket display
        # reflects the new team names immediately.
        for match in CURRENT_TOURNAMENT.matches:
            if match.participant1 and match.team1:
                match.participant1.name = match.team1.name
            if match.participant2 and match.team2:
                match.participant2.name = match.team2.name
        for match in CURRENT_TOURNAMENT.losers_bracket_matches:
            if match.participant1 and match.team1:
                match.participant1.name = match.team1.name
            if match.participant2 and match.team2:
                match.participant2.name = match.team2.name
        return tournament_save_state()
    except ValueError as e:
        return json.dumps({'error': str(e)})


@eel.expose
def tournament_rename_team(team_index: int, new_name: str) -> str:
    """
    Rename a specific team to a custom name.

    Args:
        team_index: 0-based index of the team
        new_name: New name for the team (must be unique within tournament)

    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    if team_index < 0 or team_index >= len(CURRENT_TOURNAMENT.teams):
        return json.dumps({'error': f'Team index {team_index} out of range'})

    if not new_name or not new_name.strip():
        return json.dumps({'error': 'Team name cannot be empty'})

    new_name = new_name.strip()

    # Check for uniqueness within tournament
    for i, team in enumerate(CURRENT_TOURNAMENT.teams):
        if i != team_index and team.name and team.name.strip().lower() == new_name.lower():
            return json.dumps({'error': f"Team name '{new_name}' is already used by another team"})

    CURRENT_TOURNAMENT.teams[team_index].name = new_name

    # Update stand-in participant name in matches
    for match in CURRENT_TOURNAMENT.matches:
        if match.team1 and match.team1.team_id == CURRENT_TOURNAMENT.teams[team_index].team_id:
            if match.participant1:
                match.participant1.name = new_name
        if match.team2 and match.team2.team_id == CURRENT_TOURNAMENT.teams[team_index].team_id:
            if match.participant2:
                match.participant2.name = new_name
    for match in CURRENT_TOURNAMENT.losers_bracket_matches:
        if match.team1 and match.team1.team_id == CURRENT_TOURNAMENT.teams[team_index].team_id:
            if match.participant1:
                match.participant1.name = new_name
        if match.team2 and match.team2.team_id == CURRENT_TOURNAMENT.teams[team_index].team_id:
            if match.participant2:
                match.participant2.name = new_name

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

    Also updates the corresponding entry in the saved-tournaments list so that
    reopening the app and re-selecting the tournament restores the latest
    progress (match results, winner, etc.) instead of the creation-time state.
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    settings = QSettings("rlbotgui", "tournament_save")
    serialized = CURRENT_TOURNAMENT.to_dict()
    settings.setValue("save", json.dumps(serialized))

    # Keep the saved-tournaments list entry in sync with the latest state so
    # progress isn't lost when the app is closed and the tournament is reloaded.
    list_json = settings.value(TOURNAMENTS_LIST_KEY, type=str)
    try:
        tournaments_list = json.loads(list_json) if list_json else []
    except (json.JSONDecodeError, TypeError):
        tournaments_list = []
    tournament_meta = {
        'tournament_id': CURRENT_TOURNAMENT.tournament_id,
        'name': CURRENT_TOURNAMENT.name,
        'format': CURRENT_TOURNAMENT.format,
        'participants': [p.to_dict() for p in CURRENT_TOURNAMENT.participants],
        'completed': CURRENT_TOURNAMENT.completed,
        'save_data': json.dumps(serialized)
    }
    existing_index = None
    for i, t in enumerate(tournaments_list):
        if t.get('tournament_id') == CURRENT_TOURNAMENT.tournament_id:
            existing_index = i
            break
    if existing_index is not None:
        tournaments_list[existing_index] = tournament_meta
    else:
        tournaments_list.append(tournament_meta)
    settings.setValue(TOURNAMENTS_LIST_KEY, json.dumps(tournaments_list))

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
    
    state_dict = CURRENT_TOURNAMENT.to_dict()
    return json.dumps(state_dict)


# Phase 3: LAN Match Workflow state.
# Maps match_id -> {'bot_list': full bot_list, 'match_settings': real match settings}
# for matches that are currently in the staging phase (lobby open, humans joining).
STAGING_STATE: Dict[str, Dict[str, Any]] = {}


@eel.expose
def tournament_start_match(match_id: str, use_staging: bool = False) -> str:
    """
    Start a specific match in the tournament. Launches the match automatically.

    Phase 3 LAN Match Workflow: when the match contains human participants and
    `use_staging` is True, a "staging" match is launched first (humans only,
    no bots, no instant start) so the host can set up the LAN host and let
    humans join. The real match is then launched via
    `tournament_confirm_players_ready()` with
    `Existing Match Behaviour = Continue And Spawn`.

    Args:
        match_id: ID of the match to start
        use_staging: When True and the match has humans, launch a staging
            lobby instead of the real match.

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

    # Match behavior is owned by the main GUI settings (not the tournament), so
    # read the operator's saved 'Existing Match Behaviour' choice here.
    saved_match_settings = load_settings().value(MATCH_SETTINGS_KEY, type=dict) or {}
    saved_behavior = saved_match_settings.get('match_behavior')
    if saved_behavior not in ('Restart If Different', 'Restart', 'Continue And Spawn'):
        saved_behavior = 'Restart If Different'

    # Read all non-tournament-specific settings from the main GUI so the
    # operator can change them mid-tournament without a tournament-specific option.
    saved_skip_replays = saved_match_settings.get('skip_replays', False)
    saved_auto_save_replay = saved_match_settings.get('auto_save_replay', False)
    saved_instant_start = saved_match_settings.get('instant_start', False)
    saved_enable_lockstep = saved_match_settings.get('enable_lockstep', False)
    saved_enable_rendering = saved_match_settings.get('enable_rendering', False)
    saved_enable_state_setting = saved_match_settings.get('enable_state_setting', False)

    # Determine the map for this match: either the fixed selection or a weighted
    # random pick from the game mode's pool when randomize_map is enabled.
    game_mode = CURRENT_TOURNAMENT.game_mode or 'Soccer'
    if CURRENT_TOURNAMENT.randomize_map:
        selected_map = pick_random_map(game_mode)
    else:
        selected_map = CURRENT_TOURNAMENT.map if CURRENT_TOURNAMENT.map else 'DFHStadium'

    match_settings = {
        'game_mode': game_mode,
        'map': selected_map,
        'skip_replays': saved_skip_replays,
        'instant_start': saved_instant_start,
        'enable_lockstep': saved_enable_lockstep,
        'enable_rendering': saved_enable_rendering,
        'enable_state_setting': saved_enable_state_setting,
        'auto_save_replay': saved_auto_save_replay,
        'match_behavior': saved_behavior,
        'mutators': mutators,
        'scripts': CURRENT_TOURNAMENT.scripts or [],
        'mercy_rule': CURRENT_TOURNAMENT.mercy_rule or 0
    }
    
    has_humans = match_has_humans(match)
    human_count = count_humans_in_match(match)

    # Issue 4: Staging no longer works with Rocket Plugin's LAN hosting.
    # The correct workflow is:
    # 1. Open Rocket League via RLBot
    # 2. Host uses Rocket Plugin to host LAN match
    # 3. Humans join via Rocket Plugin
    # 4. Start match with "Continue and Spawn" setting
    # 
    # When use_staging is True for human matches, we now just open RL
    # and let the user handle the rest manually.
    if has_humans and use_staging:
        # Just open RL without starting a match
        return json.dumps({
            'success': True,
            'match_id': match_id,
            'staging': False,  # No staging, just open RL
            'has_humans': True,
            'human_count': human_count,
            'message': 'Please use Rocket Plugin to host and have humans join, then start the match with Continue and Spawn',
            'participants': [match.participant1.name, match.participant2.name]
        })

    # All-bot match (or operator chose "start immediately"): launch directly.
    eel.spawn(launch_tournament_match, bot_list, match_settings, match_id)

    return json.dumps({
        'success': True,
        'match_id': match_id,
        'staging': False,
        'has_humans': has_humans,
        'human_count': human_count,
        'participants': [match.participant1.name, match.participant2.name]
    })


@eel.expose
def tournament_match_has_humans(match_id: str) -> str:
    """
    Report whether a match contains human participants (Phase 3 LAN workflow).

    Returns:
        JSON string: {'has_humans': bool, 'human_count': int}
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    match = None
    for m in CURRENT_TOURNAMENT.matches:
        if m.match_id == match_id:
            match = m
            break
    if match is None:
        for m in CURRENT_TOURNAMENT.losers_bracket_matches:
            if m.match_id == match_id:
                match = m
                break
    if match is None:
        return json.dumps({'error': f'Match {match_id} not found'})

    return json.dumps({
        'has_humans': match_has_humans(match),
        'human_count': count_humans_in_match(match)
    })


@eel.expose
def tournament_confirm_players_ready(match_id: str) -> str:
    """
    Phase 3 LAN Match Workflow: launch the real match after the operator
    confirms all humans are connected to the staging lobby.

    The real match is launched with `Existing Match Behaviour = Continue And
    Spawn` so bots are injected into the already-hosted lobby without tearing
    it down (humans stay connected).

    Args:
        match_id: ID of the match currently in the staging phase.

    Returns:
        JSON string with status
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    staging = STAGING_STATE.get(match_id)
    if staging is None:
        return json.dumps({'error': f'No staging lobby found for match {match_id}. Start the match with staging first.'})

    bot_list = staging['bot_list']
    match_settings = dict(staging['match_settings'])
    # Inject bots into the existing lobby without tearing it down.
    # Respect the user's 'Existing Match Behaviour' choice from the main GUI
    # (saved via save_match_settings). Default to 'Continue And Spawn' when
    # nothing is saved, since that is the only mode that injects bots into an
    # already-hosted lobby without restarting it.
    saved_match_settings = load_settings().value(MATCH_SETTINGS_KEY, type=dict) or {}
    saved_behavior = saved_match_settings.get('match_behavior')
    if saved_behavior in ('Restart If Different', 'Restart', 'Continue And Spawn'):
        match_settings['match_behavior'] = saved_behavior
    else:
        match_settings['match_behavior'] = 'Continue And Spawn'
    match_settings['instant_start'] = True

    del STAGING_STATE[match_id]

    eel.spawn(launch_tournament_match, bot_list, match_settings, match_id)

    return json.dumps({
        'success': True,
        'match_id': match_id,
        'real_match_launched': True
    })


@eel.expose
def tournament_cancel_staging(match_id: str) -> str:
    """
    Phase 3 LAN Match Workflow: abandon the staging lobby for a match.

    The staging lobby is left running (the operator can close it in-game);
    the tournament simply drops the pending real-match state so the match can
    be re-started later.

    Args:
        match_id: ID of the match currently in the staging phase.

    Returns:
        JSON string with status
    """
    if match_id in STAGING_STATE:
        del STAGING_STATE[match_id]
    return json.dumps({'success': True, 'match_id': match_id})


@eel.expose
def tournament_stop_match() -> str:
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
        
        # Wait a moment for the shutdown to complete
        import time
        time.sleep(0.5)
        
        # Clear match in progress state
        # Note: The match is not marked as completed, just stopped
        # User can retry the same match or start a different one
        return json.dumps({
            'success': True,
            'message': 'Match stopped successfully'
        })
    except Exception as e:
        return json.dumps({
            'error': f'Failed to stop match: {str(e)}'
        })


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


def launch_tournament_match(bot_list: list, match_settings: dict, match_id: str, wait_for_completion: bool = True):
    """
    Launch the tournament match in a separate thread.

    Args:
        bot_list: Bot/human list for the match.
        match_settings: Match settings dict.
        match_id: Tournament match ID (used for result recording).
        wait_for_completion: When False (staging match), the match is launched
            and the function returns immediately without waiting for the match
            to end or recording a result.
    """
    from rlbot_gui.match_runner.match_runner import start_match_helper
    from rlbot_gui.persistence.settings import load_settings, load_launcher_settings, launcher_preferences_from_map
    
    print(f"DEBUG: launch_tournament_match called with match_id={match_id} wait_for_completion={wait_for_completion}")
    print(f"DEBUG: bot_list={bot_list}")
    print(f"DEBUG: match_settings={match_settings}")
    
    try:
        launcher_preference_map = load_launcher_settings()
        launcher_prefs = launcher_preferences_from_map(launcher_preference_map)
        print(f"DEBUG: About to call start_match_helper")
        result_data = start_match_helper(bot_list, match_settings, launcher_prefs, wait_for_completion=wait_for_completion)
        print(f"DEBUG: start_match_helper returned result_data={result_data}")

        # Staging match: no result to record, the real match is launched later
        # via tournament_confirm_players_ready().
        if not wait_for_completion:
            print(f"DEBUG: Staging match for {match_id} launched, not waiting for completion")
            return

        team_scores = (result_data or {}).get('team_scores') or []
        player_stats = (result_data or {}).get('players') or []
        duration_seconds = (result_data or {}).get('duration_seconds')
        is_overtime = bool((result_data or {}).get('is_overtime', False))

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
                result = tournament_record_result(match_id, winner_name, json.dumps(ordered_scores),
                                                 json.dumps(player_stats) if player_stats else '[]',
                                                 duration_seconds=duration_seconds, is_overtime=is_overtime)
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
def tournament_record_result(match_id: str, winner_name: str, score_json: str, player_stats_json: str = '[]',
                             duration_seconds: Optional[int] = None, is_overtime: bool = False) -> str:
    """
    Record the result of a match and advance the winner.
    
    Args:
        match_id: ID of the match
        winner_name: Name of the winning participant
        score_json: JSON string of score tuple
        player_stats_json: JSON list of per-player stat dicts (optional)
        duration_seconds: Match duration in whole seconds (optional)
        is_overtime: Whether the match went to overtime (optional)
    
    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})
    
    score = tuple(json.loads(score_json))

    try:
        player_stats = json.loads(player_stats_json) if player_stats_json else []
    except (json.JSONDecodeError, TypeError):
        player_stats = []
    if not isinstance(player_stats, list):
        player_stats = []
    
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
    if player_stats:
        match.player_stats = player_stats
    if duration_seconds is not None:
        match.duration_seconds = duration_seconds
    match.is_overtime = is_overtime
    
    # For double elimination, populate the Losers Bracket match with the loser
    if CURRENT_TOURNAMENT.format == 'double_elimination' and match.loser_next_match_id:
        _populate_losers_bracket_match(match, winner)
    
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

    # Swiss format: special progression logic (round-based, no advancement)
    if CURRENT_TOURNAMENT.format == 'swiss':
        _handle_swiss_progression(match)
        return tournament_save_state()

    # Round robin: no advancement; winner is the top-ranked entity once all
    # matches are complete.
    if CURRENT_TOURNAMENT.format == 'round_robin':
        _handle_round_robin_progression()
        return tournament_save_state()

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


def _populate_losers_bracket_match(completed_match: Match, winner: Participant) -> None:
    """
    Populate a Losers Bracket match with the loser from a Winners Bracket match.
    
    When a Winners Bracket match completes, the loser advances to their
    corresponding Losers Bracket match. This function finds that match
    and populates it with the loser.
    
    Args:
        completed_match: The completed Winners Bracket match
        winner: The winner of the match (the loser is the other participant)
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None or CURRENT_TOURNAMENT.format != 'double_elimination':
        return
    
    loser_next_match_id = completed_match.loser_next_match_id
    if not loser_next_match_id:
        return
    
    # Find the Losers Bracket match
    lb_match = None
    for m in CURRENT_TOURNAMENT.losers_bracket_matches:
        if m.match_id == loser_next_match_id:
            lb_match = m
            break
    
    if lb_match is None:
        print(f"DEBUG: _populate_losers_bracket_match - could not find LB match {loser_next_match_id}")
        return
    
    # Determine the loser
    loser = None
    if completed_match.participant1 and completed_match.participant1 != winner:
        loser = completed_match.participant1
    elif completed_match.participant2 and completed_match.participant2 != winner:
        loser = completed_match.participant2
    
    if loser is None:
        print(f"DEBUG: _populate_losers_bracket_match - could not determine loser from match {completed_match.match_id}")
        return
    
    # Populate the Losers Bracket match with the loser
    if lb_match.participant1 is None:
        lb_match.participant1 = loser
        print(f"DEBUG: _populate_losers_bracket_match - {loser.name} assigned to {lb_match.match_id} as participant1")
    elif lb_match.participant2 is None:
        lb_match.participant2 = loser
        print(f"DEBUG: _populate_losers_bracket_match - {loser.name} assigned to {lb_match.match_id} as participant2")
    else:
        print(f"DEBUG: _populate_losers_bracket_match - {lb_match.match_id} already has both participants")
        return
    
    # For team-based matches, attach the losing team to the Losers Bracket match
    if CURRENT_TOURNAMENT.teams:
        losing_team = None
        for t in CURRENT_TOURNAMENT.teams:
            if t.team_id == loser.participant_id:
                losing_team = t
                break
        if losing_team is not None:
            if lb_match.participant1 is loser and lb_match.team1 is None:
                lb_match.team1 = losing_team
            elif lb_match.participant2 is loser and lb_match.team2 is None:
                lb_match.team2 = losing_team
    
    # Check if this LB match now has a bye situation (only 1 participant and no more feeders expected)
    # If so, auto-advance the single participant
    _check_and_handle_lb_bye(lb_match)


def _check_and_handle_lb_bye(lb_match: Match) -> None:
    """
    Check if a Losers Bracket match has a bye situation and auto-advance if needed.
    
    A bye occurs in LB when:
    1. The match has exactly 1 participant
    2. All potential feeders have been exhausted (no more participants will arrive)
    
    In this case, the single participant auto-advances to the next match.
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return
    
    # Only check matches with exactly 1 participant
    has_p1 = lb_match.participant1 is not None
    has_p2 = lb_match.participant2 is not None
    
    if has_p1 and has_p2:
        # Match has both participants - no bye
        return
    
    if not has_p1 and not has_p2:
        # Match has no participants - nothing to do
        return
    
    # Match has exactly 1 participant - check if all feeders are exhausted
    
    # Count total expected feeders (WB matches that feed into this LB match)
    # Only count WB matches that are actual matches (not byes) as they are the ones that produce losers
    wb_feeder_count = 0
    completed_wb_feeder_count = 0
    for m in CURRENT_TOURNAMENT.matches:
        if m.loser_next_match_id == lb_match.match_id:
            # Only count this feeder if it's an actual match (not a bye)
            # Bye matches are completed but never produce losers
            is_actual_match = (m.participant1 is not None and m.participant2 is not None)
            if is_actual_match:
                wb_feeder_count += 1
                if m.completed:
                    completed_wb_feeder_count += 1
    
    # Check if any previous LB match feeds into this match
    lb_feeder_count = 0
    completed_lb_feeder_count = 0
    for m in CURRENT_TOURNAMENT.losers_bracket_matches:
        if m.next_match_id == lb_match.match_id:
            lb_feeder_count += 1
            if m.completed:
                completed_lb_feeder_count += 1
    
    # Determine if all feeders are exhausted
    # All WB feeders are exhausted if all WB matches that feed here are completed
    wb_exhausted = (wb_feeder_count == 0) or (completed_wb_feeder_count == wb_feeder_count)
    
    # All LB feeders are exhausted if all LB matches that feed here are completed
    lb_exhausted = (lb_feeder_count == 0) or (completed_lb_feeder_count == lb_feeder_count)
    
    # If all feeders are exhausted and we have 1 participant, it's a bye
    if wb_exhausted and lb_exhausted:
        single_participant = lb_match.participant1 if has_p1 else lb_match.participant2
        print(f"DEBUG: _check_and_handle_lb_bye - {lb_match.match_id} has bye, advancing {single_participant.name}")
        
        # Mark the match as completed with the single participant as winner
        lb_match.completed = True
        lb_match.winner = single_participant
        
        # Advance to next match
        if lb_match.next_match_id:
            advance_winner(lb_match, single_participant)


# ---------------------------------------------------------------------------
# Phase 4: Swiss format progression
# ---------------------------------------------------------------------------

def _swiss_get_entities() -> List[Participant]:
    """
    Get the entities (stand-in participants or raw participants) used for
    Swiss pairing. In team mode, each team is represented by a stand-in
    participant whose participant_id is the team_id.
    """
    global CURRENT_TOURNAMENT
    if CURRENT_TOURNAMENT.team_size > 1 and CURRENT_TOURNAMENT.teams:
        stand_ins = []
        for t in CURRENT_TOURNAMENT.teams:
            stand_ins.append(Participant(
                name=t.name,
                participant_id=t.team_id,
                participant_type='team',
                seed=0
            ))
        return stand_ins
    return CURRENT_TOURNAMENT.participants


def _swiss_name_to_eid() -> Dict[str, str]:
    """
    Build a map of player name -> entity id so per-player stats can be
    attributed to the owning entity (participant in 1v1, team in team mode).
    """
    global CURRENT_TOURNAMENT
    mapping: Dict[str, str] = {}
    if CURRENT_TOURNAMENT.team_size > 1 and CURRENT_TOURNAMENT.teams:
        for t in CURRENT_TOURNAMENT.teams:
            for p in t.participants:
                mapping[p.name] = t.team_id
    else:
        for p in CURRENT_TOURNAMENT.participants:
            mapping[p.name] = p.participant_id
    return mapping


def _swiss_attach_teams(matches: List[Match]) -> None:
    """Attach team1/team2 data to Swiss matches in team mode."""
    global CURRENT_TOURNAMENT
    if CURRENT_TOURNAMENT.team_size <= 1 or not CURRENT_TOURNAMENT.teams:
        return
    team_by_id = {t.team_id: t for t in CURRENT_TOURNAMENT.teams}
    for match in matches:
        if match.participant1 and match.participant1.participant_id in team_by_id:
            match.team1 = team_by_id[match.participant1.participant_id]
        if match.participant2 and match.participant2.participant_id in team_by_id:
            match.team2 = team_by_id[match.participant2.participant_id]


def _swiss_declare_winner(winner: Participant) -> None:
    """Set the tournament winner (and winning team in team mode)."""
    global CURRENT_TOURNAMENT
    CURRENT_TOURNAMENT.winner = winner
    if CURRENT_TOURNAMENT.team_size > 1 and CURRENT_TOURNAMENT.teams:
        for t in CURRENT_TOURNAMENT.teams:
            if t.team_id == winner.participant_id:
                CURRENT_TOURNAMENT.winner_team = t
                break
    CURRENT_TOURNAMENT.completed = True


def _handle_swiss_progression(completed_match: Match) -> None:
    """
    Advance the Swiss tournament after a match completes.

    Logic:
    - If the completed match is the playoff (round > swiss_rounds), the
      tournament is over — the winner was already recorded.
    - Otherwise, check if all matches in the current round are complete:
      - If more rounds remain, generate the next round.
      - If all rounds are complete, determine the winner via tiebreakers,
        or schedule a head-to-head playoff if the top 2 are tied.
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None or CURRENT_TOURNAMENT.format != 'swiss':
        return

    # Playoff match completed: tournament is over.
    if completed_match.round_num > CURRENT_TOURNAMENT.swiss_rounds:
        print(f"DEBUG: Swiss playoff match {completed_match.match_id} complete, tournament over")
        if completed_match.winner is not None:
            _swiss_declare_winner(completed_match.winner)
        return

    # Check if all matches in the current round are complete.
    round_matches = [m for m in CURRENT_TOURNAMENT.matches if m.round_num == completed_match.round_num]
    if not all(m.completed for m in round_matches):
        print(f"DEBUG: Swiss round {completed_match.round_num} not yet complete")
        return

    print(f"DEBUG: Swiss round {completed_match.round_num} complete")

    if completed_match.round_num < CURRENT_TOURNAMENT.swiss_rounds:
        # Generate the next round based on current records.
        entities = _swiss_get_entities()
        completed = [m for m in CURRENT_TOURNAMENT.matches if m.completed]
        next_round = completed_match.round_num + 1
        new_matches = generate_swiss_next_round(
            entities, completed, next_round, _swiss_name_to_eid()
        )
        _swiss_attach_teams(new_matches)
        CURRENT_TOURNAMENT.matches.extend(new_matches)
        CURRENT_TOURNAMENT.current_round = next_round
        print(f"DEBUG: Swiss round {next_round} generated with {len(new_matches)} matches")
    else:
        # All rounds complete: determine winner or schedule a playoff.
        entities = _swiss_get_entities()
        completed = [m for m in CURRENT_TOURNAMENT.matches if m.completed]
        result = determine_swiss_winner(entities, completed, _swiss_name_to_eid())

        if result['playoff_needed'] and not CURRENT_TOURNAMENT.swiss_playoff_scheduled:
            p1, p2 = result['playoff_participants']
            playoff = Match(
                match_id="SW_PLAYOFF",
                round_num=CURRENT_TOURNAMENT.swiss_rounds + 1,
                participant1=p1,
                participant2=p2,
                completed=False
            )
            _swiss_attach_teams([playoff])
            CURRENT_TOURNAMENT.matches.append(playoff)
            CURRENT_TOURNAMENT.swiss_playoff_scheduled = True
            CURRENT_TOURNAMENT.current_round = CURRENT_TOURNAMENT.swiss_rounds + 1
            print(f"DEBUG: Swiss playoff scheduled: {p1.name} vs {p2.name}")
        else:
            winner = result['winner']
            if winner is not None:
                print(f"DEBUG: Swiss winner determined: {winner.name}")
                _swiss_declare_winner(winner)
            else:
                # Should not happen, but guard against it.
                print(f"DEBUG: Swiss winner could not be determined")


def _handle_round_robin_progression() -> None:
    """
    Advance the round robin tournament after a match completes.

    Round robin has no bracket advancement: once every match is complete,
    the winner is the top-ranked entity (wins, then multi-way head-to-head,
    goal difference, goals for, score).
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None or CURRENT_TOURNAMENT.format != 'round_robin':
        return

    if CURRENT_TOURNAMENT.completed:
        return

    if not all(m.completed for m in CURRENT_TOURNAMENT.matches):
        return

    print("DEBUG: Round robin all matches complete, determining winner")
    entities = _swiss_get_entities()
    completed = [m for m in CURRENT_TOURNAMENT.matches if m.completed]
    ordered, _ = rank_entities(entities, completed, _swiss_name_to_eid())
    if ordered:
        winner = ordered[0]
        print(f"DEBUG: Round robin winner: {winner.name}")
        _swiss_declare_winner(winner)


def is_tournament_final_match(match: Match) -> bool:
    """
    Check if this is the final match of the tournament.
    
    A match is the final if the winner doesn't advance to another match
    (i.e., next_match_id is None and loser_next_match_id is None).
    
    For double elimination:
    - The Grand Final is the final match where the winner is the tournament champion
    """
    # If the match has no next match and no loser_next_match_id, it's the final
    is_final = match.next_match_id is None and match.loser_next_match_id is None
    print(f"DEBUG: is_tournament_final_match({match.match_id}) = {is_final} (next_match_id={match.next_match_id}, loser_next_match_id={match.loser_next_match_id})")
    return is_final


def advance_winner(match: Match, winner: Participant) -> None:
    """
    Advance the winner to their next match.
    
    For double elimination:
    - Winners Bracket match winner advances to next WB match
    - Losers Bracket match winner advances to next LB match or Grand Final
    - Grand Final winner is the tournament champion
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return
    
    next_match_id = match.next_match_id
    if next_match_id is None:
        print(f"DEBUG: advance_winner({match.match_id}) - no next match, winner {winner.name} is tournament champion")
        return
    
    print(f"DEBUG: advance_winner({match.match_id}) - advancing {winner.name} to match {next_match_id}")
    
    # Find next match in both winners and losers bracket
    next_match = None
    for m in CURRENT_TOURNAMENT.matches:
        if m.match_id == next_match_id:
            next_match = m
            break
    
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
    
    # Check if next match has a bye situation
    _handle_bye_situation(next_match)


def _handle_bye_situation(next_match: Match) -> None:
    """
    Handle bye situations in any round.
    
    A bye occurs when:
    1. A match has only 1 participant and the other slot feeds from a completed bye match
    2. A match has only 1 participant and there's no other feeder (odd number of participants)
    3. A match has only 1 participant and all pending feeders are WB bye matches that won't produce losers
    
    In both cases, the single participant should automatically advance.
    """
    global CURRENT_TOURNAMENT
    
    if CURRENT_TOURNAMENT is None:
        return
    
    # Check if next match has only 1 participant
    if next_match.participant1 is not None and next_match.participant2 is None:
        # Check all feeders to find any completed bye matches that haven't been processed
        completed_feeder = _find_completed_unprocessed_feeder(next_match)
        
        if completed_feeder is not None and completed_feeder.winner:
            # The other feeder is a completed bye - advance that winner
            print(f"DEBUG: _handle_bye_situation - advancing bye winner {completed_feeder.winner.name} from {completed_feeder.match_id}")
            advance_winner(completed_feeder, completed_feeder.winner)
        else:
            # No completed unprocessed feeder - check if there's no other feeder at all
            # (this is a bye in a later round) OR all pending feeders are WB byes that won't produce losers
            all_feeders = _get_all_feeders(next_match)
            
            # Check if there are any pending (uncompleted) feeders that will actually produce participants
            has_pending_real_feeders = False
            for feeder in all_feeders:
                # For WB matches, check if they will produce a loser
                if feeder.loser_next_match_id == next_match.match_id:
                    # A WB match is a "true bye" if it has exactly 1 participant (will produce no loser)
                    # A WB match that has 0 participants is "not yet populated" and will produce a loser
                    has_p1 = feeder.participant1 is not None
                    has_p2 = feeder.participant2 is not None
                    
                    if has_p1 and has_p2:
                        # Actual match - will produce a loser when completed
                        if not feeder.completed:
                            has_pending_real_feeders = True
                            break
                    elif not has_p1 and not has_p2:
                        # Not yet populated - will eventually have participants and produce a loser
                        has_pending_real_feeders = True
                        break
                    # else: has exactly 1 participant - this is a bye, won't produce a loser
                
                # For LB matches, only count uncompleted feeders
                if feeder.next_match_id == next_match.match_id and not feeder.completed:
                    has_pending_real_feeders = True
                    break
            
            if len(all_feeders) == 0 or not has_pending_real_feeders:
                # No other feeder - this is a bye in a later round
                # The single participant advances automatically
                print(f"DEBUG: _handle_bye_situation - later round bye for {next_match.participant1.name} in {next_match.match_id}")
                next_match.completed = True
                next_match.winner = next_match.participant1
                if next_match.next_match_id:
                    advance_winner(next_match, next_match.participant1)
    elif next_match.participant1 is None and next_match.participant2 is not None:
        # Same logic, just swapped
        completed_feeder = _find_completed_unprocessed_feeder(next_match)
        
        if completed_feeder is not None and completed_feeder.winner:
            print(f"DEBUG: _handle_bye_situation - advancing bye winner {completed_feeder.winner.name} from {completed_feeder.match_id}")
            advance_winner(completed_feeder, completed_feeder.winner)
        else:
            all_feeders = _get_all_feeders(next_match)
            
            # Check if there are any pending (uncompleted) feeders that will actually produce participants
            has_pending_real_feeders = False
            for feeder in all_feeders:
                # For WB matches, check if they will produce a loser
                if feeder.loser_next_match_id == next_match.match_id:
                    # A WB match is a "true bye" if it has exactly 1 participant (will produce no loser)
                    # A WB match that has 0 participants is "not yet populated" and will produce a loser
                    has_p1 = feeder.participant1 is not None
                    has_p2 = feeder.participant2 is not None
                    
                    if has_p1 and has_p2:
                        # Actual match - will produce a loser when completed
                        if not feeder.completed:
                            has_pending_real_feeders = True
                            break
                    elif not has_p1 and not has_p2:
                        # Not yet populated - will eventually have participants and produce a loser
                        has_pending_real_feeders = True
                        break
                    # else: has exactly 1 participant - this is a bye, won't produce a loser
                
                # For LB matches, only count uncompleted feeders
                if feeder.next_match_id == next_match.match_id and not feeder.completed:
                    has_pending_real_feeders = True
                    break
            
            if len(all_feeders) == 0 or not has_pending_real_feeders:
                print(f"DEBUG: _handle_bye_situation - later round bye for {next_match.participant2.name} in {next_match.match_id}")
                next_match.completed = True
                next_match.winner = next_match.participant2
                if next_match.next_match_id:
                    advance_winner(next_match, next_match.participant2)


def _get_all_feeders(match: Match) -> List[Match]:
    """
    Get all matches that feed into the given match.
    
    In double elimination, matches can receive participants from two sources:
    - Winners Bracket losers via loser_next_match_id
    - Losers Bracket winners via next_match_id
    
    This function checks both fields to correctly identify all feeder matches,
    preventing premature bye triggering when a match is waiting for a WB loser.
    """
    feeders = []
    for m in CURRENT_TOURNAMENT.matches:
        if m.next_match_id == match.match_id or m.loser_next_match_id == match.match_id:
            feeders.append(m)
    
    # Also check losers bracket
    for m in CURRENT_TOURNAMENT.losers_bracket_matches:
        if m.next_match_id == match.match_id or m.loser_next_match_id == match.match_id:
            feeders.append(m)
    
    return feeders


def _find_completed_unprocessed_feeder(match: Match) -> Optional[Match]:
    """
    Find a feeder match that is completed (has a winner) but hasn't been processed
    (i.e., the winner hasn't been placed in this match yet).
    """
    feeders = _get_all_feeders(match)
    
    for feeder in feeders:
        # Check if feeder is completed with a winner
        if feeder.completed and feeder.winner:
            # Check if this winner is already in the next match
            if match.participant1 != feeder.winner and match.participant2 != feeder.winner:
                # The winner hasn't been placed in this match yet
                return feeder
    
    return None


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
        teams = form_teams_random(shuffled, CURRENT_TOURNAMENT.team_size,
                                 allow_duplicates=CURRENT_TOURNAMENT.allow_duplicates)
        CURRENT_TOURNAMENT.teams = teams
        matches, losers_matches, grand_final_match = generate_team_bracket(teams, CURRENT_TOURNAMENT.format)
        CURRENT_TOURNAMENT.matches = matches
        CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
        if grand_final_match:
            CURRENT_TOURNAMENT.matches.append(grand_final_match)
    elif CURRENT_TOURNAMENT.format == 'single_elimination':
        matches, num_rounds = generate_single_elimination_bracket(shuffled)
        CURRENT_TOURNAMENT.matches = matches
    elif CURRENT_TOURNAMENT.format == 'double_elimination':
        winners_matches, losers_matches, grand_final_match, num_rounds = generate_double_elimination_bracket(shuffled)
        CURRENT_TOURNAMENT.matches = winners_matches
        CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
        if grand_final_match:
            CURRENT_TOURNAMENT.matches.append(grand_final_match)
    elif CURRENT_TOURNAMENT.format == 'round_robin':
        matches = generate_round_robin_bracket(shuffled)
        CURRENT_TOURNAMENT.matches = matches
    elif CURRENT_TOURNAMENT.format == 'swiss':
        matches = generate_swiss_round1(shuffled)
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


# ---------------------------------------------------------------------------
# Phase 3: Tournament Templates
# A template captures the creation-time configuration of a tournament
# (name, format, team size, allow_duplicates, mutators, human count/names)
# so operators can quickly spin up similar tournaments.
# ---------------------------------------------------------------------------
TEMPLATES_KEY = "tournament_templates"


def _load_templates() -> List[Dict[str, Any]]:
    settings = QSettings("rlbotgui", "tournament_save")
    list_json = settings.value(TEMPLATES_KEY, type=str)
    try:
        return json.loads(list_json) if list_json else []
    except (json.JSONDecodeError, TypeError):
        return []


def _save_templates(templates: List[Dict[str, Any]]) -> None:
    settings = QSettings("rlbotgui", "tournament_save")
    settings.setValue(TEMPLATES_KEY, json.dumps(templates))


@eel.expose
def tournament_save_template(template_name: str, template_json: str) -> str:
    """
    Save a tournament template (creation-time configuration).

    Args:
        template_name: Display name for the template.
        template_json: JSON string of the template config:
            {
              'format': 'single_elimination',
              'team_size': 2,
              'allow_duplicates': false,
              'mutators': {...},
              'human_count': 0,
              'human_names': []
            }

    Returns:
        JSON string with the saved template.
    """
    try:
        config = json.loads(template_json) if template_json else {}
    except (json.JSONDecodeError, TypeError) as e:
        return json.dumps({'error': f'Invalid template JSON: {e}'})

    if not template_name or not template_name.strip():
        return json.dumps({'error': 'Template name is required'})

    templates = _load_templates()
    template = {
        'template_id': str(uuid.uuid4())[:8],
        'name': template_name.strip(),
        'config': config,
        'created_at': datetime.now().isoformat()
    }

    # Replace an existing template with the same name, otherwise append.
    existing = next((t for t in templates if t['name'].lower() == template['name'].lower()), None)
    if existing is not None:
        existing['config'] = config
        existing['created_at'] = template['created_at']
    else:
        templates.append(template)

    _save_templates(templates)
    return json.dumps({'success': True, 'template': template})


@eel.expose
def tournament_get_templates() -> str:
    """
    List all saved tournament templates.

    Returns:
        JSON string of the template list.
    """
    return json.dumps(_load_templates())


@eel.expose
def tournament_delete_template(template_id: str) -> str:
    """
    Delete a tournament template by ID.

    Args:
        template_id: ID of the template to delete.

    Returns:
        JSON string with status.
    """
    templates = _load_templates()
    templates = [t for t in templates if t['template_id'] != template_id]
    _save_templates(templates)
    return json.dumps({'success': True})


@eel.expose
def tournament_get_statistics() -> str:
    """
    Phase 3: Compute tournament statistics from completed matches.

    Returns per-participant (or per-team) stats:
      - matches_played, wins, losses, draws
      - goals_for, goals_against, goal_difference
      - win_rate (0.0-1.0)
      - score, assists, saves, shots, demolitions, own_goals (aggregated from
        per-player stats captured from each match's final game tick packet)
    Plus overall tournament stats:
      - total_matches, completed_matches, total_goals

    The 'ranked' list is ordered by wins (descending); ties are broken by
    multi-way head-to-head (wins among the tied group), then goal
    difference, then goals for, then score.

    Returns:
        JSON string with the statistics report.
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    # Determine the entity list: teams in team mode, participants in 1v1.
    is_team_mode = (CURRENT_TOURNAMENT.team_size > 1 and
                    len(CURRENT_TOURNAMENT.teams) > 0)

    if is_team_mode:
        entities = {t.team_id: {'name': t.name, 'type': 'team'} for t in CURRENT_TOURNAMENT.teams}
    else:
        entities = {p.participant_id: {'name': p.name, 'type': p.participant_type}
                    for p in CURRENT_TOURNAMENT.participants}

    # Map participant name -> entity id so per-player stats can be attributed to
    # the right participant (1v1) or team (team mode).
    name_to_eid: Dict[str, str] = {}
    if is_team_mode:
        for t in CURRENT_TOURNAMENT.teams:
            for p in t.participants:
                name_to_eid[p.name] = t.team_id
    else:
        for p in CURRENT_TOURNAMENT.participants:
            name_to_eid[p.name] = p.participant_id

    stats = {
        eid: {
            'name': info['name'],
            'type': info['type'],
            'matches_played': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'goals_for': 0,
            'goals_against': 0,
            'goal_difference': 0,
            'win_rate': 0.0,
            # Aggregated per-player stats (from each match's final packet)
            'score': 0,
            'assists': 0,
            'saves': 0,
            'shots': 0,
            'demolitions': 0,
            'own_goals': 0
        } for eid, info in entities.items()
    }

    total_goals = 0
    completed_matches = 0

    all_matches = list(CURRENT_TOURNAMENT.matches) + list(CURRENT_TOURNAMENT.losers_bracket_matches)
    for match in all_matches:
        if not match.completed or not match.score:
            continue
        if not match.participant1 or not match.participant2:
            continue
        completed_matches += 1

        p1_id = match.participant1.participant_id
        p2_id = match.participant2.participant_id
        s1, s2 = match.score[0], match.score[1]
        total_goals += s1 + s2

        if p1_id in stats:
            stats[p1_id]['matches_played'] += 1
            stats[p1_id]['goals_for'] += s1
            stats[p1_id]['goals_against'] += s2
        if p2_id in stats:
            stats[p2_id]['matches_played'] += 1
            stats[p2_id]['goals_for'] += s2
            stats[p2_id]['goals_against'] += s1

        # Aggregate per-player stats onto the owning entity.
        for ps in (match.player_stats or []):
            eid = name_to_eid.get(ps.get('name'))
            if eid is None or eid not in stats:
                continue
            s = stats[eid]
            s['score'] += int(ps.get('score', 0) or 0)
            s['assists'] += int(ps.get('assists', 0) or 0)
            s['saves'] += int(ps.get('saves', 0) or 0)
            s['shots'] += int(ps.get('shots', 0) or 0)
            s['demolitions'] += int(ps.get('demolitions', 0) or 0)
            s['own_goals'] += int(ps.get('own_goals', 0) or 0)

        if s1 > s2:
            if p1_id in stats:
                stats[p1_id]['wins'] += 1
            if p2_id in stats:
                stats[p2_id]['losses'] += 1
        elif s2 > s1:
            if p2_id in stats:
                stats[p2_id]['wins'] += 1
            if p1_id in stats:
                stats[p1_id]['losses'] += 1
        else:
            if p1_id in stats:
                stats[p1_id]['draws'] += 1
            if p2_id in stats:
                stats[p2_id]['draws'] += 1

    # Finalize derived stats
    for eid, s in stats.items():
        s['goal_difference'] = s['goals_for'] - s['goals_against']
        if s['matches_played'] > 0:
            s['win_rate'] = round(s['wins'] / s['matches_played'], 3)

    # Rank entities: wins desc, then multi-way head-to-head, then goal
    # difference, goals for, and score.
    entity_objs = [
        Participant(name=info['name'], participant_id=eid,
                    participant_type=info['type'], seed=0)
        for eid, info in entities.items()
    ]
    ordered, _ = rank_entities(entity_objs, all_matches, name_to_eid)
    ranked = [stats[e.participant_id] for e in ordered]

    return json.dumps({
        'tournament_name': CURRENT_TOURNAMENT.name,
        'format': CURRENT_TOURNAMENT.format,
        'team_size': CURRENT_TOURNAMENT.team_size,
        'total_matches': len(all_matches),
        'completed_matches': completed_matches,
        'total_goals': total_goals,
        'completed': CURRENT_TOURNAMENT.completed,
        'winner': CURRENT_TOURNAMENT.winner.name if CURRENT_TOURNAMENT.winner else None,
        'winner_team': CURRENT_TOURNAMENT.winner_team.name if CURRENT_TOURNAMENT.winner_team else None,
        'ranked': ranked
    })


def _match_entity_name(match: Match, side: int) -> Optional[str]:
    """
    Return the display name for one side of a match.

    side=0 → team1/participant1, side=1 → team2/participant2.
    Handles both team-based matches (team1/team2) and 1v1 matches
    (participant1/participant2).
    """
    if side == 0:
        if match.team1 is not None:
            return match.team1.name or 'Team'
        if match.participant1 is not None:
            return match.participant1.name
    else:
        if match.team2 is not None:
            return match.team2.name or 'Team'
        if match.participant2 is not None:
            return match.participant2.name
    return None


def _match_winner_name(match: Match) -> Optional[str]:
    """Return the winner's display name for a completed match."""
    if match.winner_team is not None:
        return match.winner_team.name or 'Team'
    if match.winner is not None:
        return match.winner.name
    return None


@eel.expose
def tournament_get_match_history() -> str:
    """
    Phase 4: Return the full match history grouped by round.

    Each match entry includes:
      - match_id, round_num, completed
      - team1_name / team2_name (or participant1_name / participant2_name)
      - score (list of two ints, or None)
      - winner_name
      - goals_for / goals_against per side (for expandable stats)

    Returns:
        JSON string with:
          - tournament_name, format, team_size
          - rounds: [{round_num, matches: [...]}] sorted by round_num
          - total_matches, completed_matches
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    all_matches = list(CURRENT_TOURNAMENT.matches) + list(CURRENT_TOURNAMENT.losers_bracket_matches)

    # Group matches by bracket + round number. For double elimination, winners
    # bracket and losers bracket rounds are listed separately so the history
    # labels match the bracket view. The Grand Final is stored in the main
    # matches array but is L-prefixed, so classify by match_id prefix.
    groups: List[tuple] = []  # (bracket, round_num, matches)
    if CURRENT_TOURNAMENT.format == 'double_elimination':
        wb_map: Dict[int, list] = {}
        lb_map: Dict[int, list] = {}
        for match in list(CURRENT_TOURNAMENT.matches) + list(CURRENT_TOURNAMENT.losers_bracket_matches):
            if match.match_id.startswith('L'):
                lb_map.setdefault(match.round_num, []).append(match)
            else:
                wb_map.setdefault(match.round_num, []).append(match)
        for round_num in sorted(wb_map.keys()):
            groups.append(('winners', round_num, wb_map[round_num]))
        for round_num in sorted(lb_map.keys()):
            groups.append(('losers', round_num, lb_map[round_num]))
    else:
        rounds_map: Dict[int, list] = {}
        for match in all_matches:
            rounds_map.setdefault(match.round_num, []).append(match)
        for round_num in sorted(rounds_map.keys()):
            groups.append(('main', round_num, rounds_map[round_num]))

    completed_matches = 0
    rounds_out = []
    for bracket, round_num, round_matches in groups:
        matches_out = []
        for match in round_matches:
            # A bye is a match that was auto-completed without ever having
            # both sides populated (never actually played). Works for both
            # 1v1 (participant slots) and team mode (team slots).
            side1_filled = match.team1 is not None or match.participant1 is not None
            side2_filled = match.team2 is not None or match.participant2 is not None
            is_bye = side1_filled != side2_filled
            entry = {
                'match_id': match.match_id,
                'round_num': match.round_num,
                'completed': match.completed,
                'is_bye': is_bye,
                'team1_name': _match_entity_name(match, 0),
                'team2_name': _match_entity_name(match, 1),
                'participant1_name': match.participant1.name if match.participant1 else None,
                'participant2_name': match.participant2.name if match.participant2 else None,
                'score': list(match.score) if match.score else None,
                'winner_name': _match_winner_name(match) if match.completed else None,
                'player_stats': match.player_stats or [],
                'duration_seconds': match.duration_seconds,
                'is_overtime': match.is_overtime,
            }
            if match.completed:
                completed_matches += 1
            matches_out.append(entry)
        rounds_out.append({
            'round_num': round_num,
            'bracket': bracket,
            'matches': matches_out
        })

    return json.dumps({
        'tournament_name': CURRENT_TOURNAMENT.name,
        'format': CURRENT_TOURNAMENT.format,
        'team_size': CURRENT_TOURNAMENT.team_size,
        'total_matches': len(all_matches),
        'completed_matches': completed_matches,
        'completed': CURRENT_TOURNAMENT.completed,
        'winner': CURRENT_TOURNAMENT.winner.name if CURRENT_TOURNAMENT.winner else None,
        'winner_team': CURRENT_TOURNAMENT.winner_team.name if CURRENT_TOURNAMENT.winner_team else None,
        'rounds': rounds_out
    })


@eel.expose
def tournament_get_swiss_standings() -> str:
    """
    Phase 4: Compute live Swiss standings ranked by wins, with ties broken
    by multi-way head-to-head, then goal difference, goals for, and score.

    Returns:
        JSON string with:
          - standings: ranked list of {name, wins, losses, draws,
            goals_for, goals_against, goal_difference, score, played, rank}
          - playoff_needed: True if the top 2 are tied and a playoff is
            required after all rounds
          - playoff_participants: [name1, name2] when playoff_needed
          - swiss_rounds, current_round
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    if CURRENT_TOURNAMENT.format != 'swiss':
        return json.dumps({'error': 'Tournament is not in Swiss format'})

    entities = _swiss_get_entities()
    completed = [m for m in CURRENT_TOURNAMENT.matches if m.completed]

    standings = calculate_swiss_standings(entities, completed, _swiss_name_to_eid())

    # Determine whether a playoff will be needed once all rounds are done.
    all_rounds_done = (CURRENT_TOURNAMENT.current_round > CURRENT_TOURNAMENT.swiss_rounds)
    playoff_needed = False
    playoff_participants = []
    if all_rounds_done and not CURRENT_TOURNAMENT.completed:
        result = determine_swiss_winner(entities, completed, _swiss_name_to_eid())
        playoff_needed = result['playoff_needed']
        playoff_participants = [p.name for p in result['playoff_participants']]

    return json.dumps({
        'standings': [
            {
                'name': s['participant'].name,
                'participant_id': s['participant'].participant_id,
                'rank': s['rank'],
                'wins': s['wins'],
                'losses': s['losses'],
                'draws': s['draws'],
                'goals_for': s['goals_for'],
                'goals_against': s['goals_against'],
                'goal_difference': s['goal_difference'],
                'score': s['score'],
                'played': s['played']
            }
            for s in standings
        ],
        'playoff_needed': playoff_needed,
        'playoff_participants': playoff_participants,
        'swiss_rounds': CURRENT_TOURNAMENT.swiss_rounds,
        'current_round': CURRENT_TOURNAMENT.current_round,
        'completed': CURRENT_TOURNAMENT.completed,
        'winner': CURRENT_TOURNAMENT.winner.name if CURRENT_TOURNAMENT.winner else None
    })


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


# Phase 4: Seeding Editor + Manual Team Pairing

@eel.expose
def tournament_set_participant_seed(participant_id: str, new_seed: int) -> str:
    """
    Set the seed value for a specific participant.
    Used by the seeding editor to reorder participants.

    Args:
        participant_id: ID of the participant to update
        new_seed: New seed value (0-based index)

    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    # Find the participant
    target = None
    for p in CURRENT_TOURNAMENT.participants:
        if p.participant_id == participant_id:
            target = p
            break

    if target is None:
        return json.dumps({'error': f'Participant {participant_id} not found'})

    # Reorder the participants list based on seed
    # Remove the target and insert at the new position
    CURRENT_TOURNAMENT.participants.remove(target)
    CURRENT_TOURNAMENT.participants.insert(new_seed, target)

    # Reassign seed values to maintain consistency
    for i, p in enumerate(CURRENT_TOURNAMENT.participants):
        p.seed = i

    return tournament_save_state()


@eel.expose
def tournament_swap_seeds(participant_id1: str, participant_id2: str) -> str:
    """
    Swap the positions of two participants in the seeding order.
    This is the primary operation for the click-to-swap seeding editor.

    Args:
        participant_id1: ID of first participant
        participant_id2: ID of second participant

    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    # Find both participants
    p1 = None
    p2 = None
    idx1 = -1
    idx2 = -1

    for i, p in enumerate(CURRENT_TOURNAMENT.participants):
        if p.participant_id == participant_id1:
            p1 = p
            idx1 = i
        if p.participant_id == participant_id2:
            p2 = p
            idx2 = i

    if p1 is None:
        return json.dumps({'error': f'Participant {participant_id1} not found'})
    if p2 is None:
        return json.dumps({'error': f'Participant {participant_id2} not found'})

    # Swap positions
    CURRENT_TOURNAMENT.participants[idx1], CURRENT_TOURNAMENT.participants[idx2] = \
        CURRENT_TOURNAMENT.participants[idx2], CURRENT_TOURNAMENT.participants[idx1]

    # Reassign seed values
    for i, p in enumerate(CURRENT_TOURNAMENT.participants):
        p.seed = i

    return tournament_save_state()


@eel.expose
def tournament_form_teams_with_pairings(pairings_json: str, team_names_json: str = '[]') -> str:
    """
    Form teams using manual pairings.

    Args:
        pairings_json: JSON array of pairing objects, each with
            {participant_id1, participant_id2}
        team_names_json: Optional JSON array of custom team names

    Returns:
        JSON string of updated tournament state
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    if CURRENT_TOURNAMENT.team_size <= 1:
        return json.dumps({'error': 'Manual team pairing only applies when team size > 1'})

    from rlbot_gui.tournament.team_manager import form_teams_with_manual_pairings

    # Parse pairings
    try:
        pairings_data = json.loads(pairings_json)
        pairings = [(p['participant_id1'], p['participant_id2']) for p in pairings_data]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return json.dumps({'error': f'Invalid pairings format: {str(e)}'})

    # Form teams with pairings
    teams, errors = form_teams_with_manual_pairings(
        CURRENT_TOURNAMENT.participants,
        pairings,
        CURRENT_TOURNAMENT.team_size,
        CURRENT_TOURNAMENT.allow_duplicates
    )

    if errors:
        return json.dumps({'error': '; '.join(errors)})

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
    matches, losers_matches, grand_final_match = generate_team_bracket(teams, CURRENT_TOURNAMENT.format)
    CURRENT_TOURNAMENT.matches = matches
    CURRENT_TOURNAMENT.losers_bracket_matches = losers_matches
    if grand_final_match:
        CURRENT_TOURNAMENT.matches.append(grand_final_match)
    CURRENT_TOURNAMENT.current_round = 1
    CURRENT_TOURNAMENT.completed = False
    CURRENT_TOURNAMENT.winner = None
    CURRENT_TOURNAMENT.winner_team = None

    return tournament_save_state()


@eel.expose
def tournament_get_current_seeding() -> str:
    """
    Get the current seeding order of participants.

    Returns:
        JSON string of participant list in current seed order
    """
    global CURRENT_TOURNAMENT

    if CURRENT_TOURNAMENT is None:
        return json.dumps({'error': 'No tournament loaded'})

    # Return participants in current order (already sorted by seed)
    participants_data = [p.to_dict() for p in CURRENT_TOURNAMENT.participants]
    return json.dumps(participants_data)
