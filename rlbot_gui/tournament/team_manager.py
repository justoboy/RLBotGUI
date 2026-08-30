"""
Team formation and team-based bracket logic for tournaments.

Supports 1v1, 2v2, 3v3, 4v4, and 5v5 team sizes.
"""
import random
import string
import uuid
from typing import List, Optional, Tuple

from rlbot_gui.tournament.tournament_state import Participant, Team, Match
from rlbot_gui.tournament.bracket_generator import (
    generate_single_elimination_bracket,
    generate_double_elimination_bracket,
    generate_round_robin_bracket
)

VALID_TEAM_SIZES = (1, 2, 3, 4, 5)
MAX_PARTICIPANTS_PER_TEAM = 5  # Rocket League has 5 kickoff spawns per side (max 5v5)

# Phase 4: Random team names.
# 15 descriptors x 15 nouns = 225 unique combinations (well over the 100+ requirement).
# Pattern: "<Descriptor> <Noun>" (e.g., "Raging Wolves", "Soaring Ravens").
TEAM_NAME_DESCRIPTORS = (
    'Blue', 'Red', 'Golden', 'Silver', 'Dark', 'Raging', 'Soaring', 'Fierce',
    'Swift', 'Iron', 'Crimson', 'Shadow', 'Thunder', 'Mystic', 'Blazing'
)
TEAM_NAME_NOUNS = (
    'Eagles', 'Ravens', 'Wolves', 'Tigers', 'Dragons', 'Knights', 'Titans',
    'Phantoms', 'Vipers', 'Comets', 'Storms', 'Rockets', 'Falcons', 'Bears', 'Serpents'
)


def _new_team_id() -> str:
    return 'T' + uuid.uuid4().hex[:8]


def _team_name(index: int) -> str:
    """Generate a default team name like 'Team A', 'Team B', ..."""
    return f"Team {string.ascii_uppercase[index] if index < 26 else index + 1}"


def validate_team_formation(num_participants: int, team_size: int, allow_duplicates: bool = False) -> Tuple[bool, str]:
    """
    Validate that participants can be split into full teams.

    Args:
        num_participants: Number of participants in the pool.
        team_size: Number of participants per team.
        allow_duplicates: When True (party mode), each participant becomes one
            team (duplicated internally), so only >= 2 participants are needed.

    Returns:
        (is_valid, error_message)
    """
    if team_size not in VALID_TEAM_SIZES:
        return False, f"Team size must be one of {VALID_TEAM_SIZES}"
    if allow_duplicates:
        if num_participants < 2:
            return False, (
                f"Need at least 2 participants (one per team) for duplicate mode, "
                f"got {num_participants}"
            )
        return True, ''
    if num_participants < team_size * 2:
        return False, (
            f"Need at least {team_size * 2} participants "
            f"({team_size} per team x 2 teams), got {num_participants}"
        )
    if num_participants % team_size != 0:
        missing = team_size - (num_participants % team_size)
        return False, (
            f"Participant count ({num_participants}) is not divisible by team size "
            f"({team_size}). Add {missing} more participant(s) to form full teams."
        )
    return True, ''


def form_teams_random(participants: List[Participant], team_size: int, allow_duplicates: bool = False) -> List[Team]:
    """
    Form teams by randomly shuffling participants and chunking into teams.

    Args:
        participants: List of participants to form teams from.
        team_size: Number of participants per team.
        allow_duplicates: If True, each participant is duplicated team_size times
            to form a team (e.g., bot1+bot1 for 2v2). This enables party-mode
            style tournaments where fewer unique bots are needed.
    """
    shuffled = list(participants)
    random.shuffle(shuffled)
    if allow_duplicates:
        teams = _chunk_into_duplicate_teams(shuffled, team_size)
    else:
        teams = _chunk_into_teams(shuffled, team_size)
    assign_random_team_names(teams)
    return teams


def form_teams_seeded(participants: List[Participant], team_size: int, allow_duplicates: bool = False) -> List[Team]:
    """
    Form teams using a snake draft based on participant seed order.
    Seed 1 goes to team 1, seed 2 to team 2, ... then back down.
    This spreads top seeds across teams for balance.

    Args:
        participants: List of participants to form teams from.
        team_size: Number of participants per team.
        allow_duplicates: If True, each participant is duplicated team_size times
            to form a team (e.g., bot1+bot1 for 2v2). Requires len(participants)
            == number of teams (not team_size * number of teams).
    """
    ordered = sorted(participants, key=lambda p: p.seed)

    if allow_duplicates:
        # Each participant becomes one team (duplicated internally)
        num_teams = len(ordered)
        teams: List[Team] = [
            Team(team_id=_new_team_id(), name=_team_name(i))
            for i in range(num_teams)
        ]
        for i, p in enumerate(ordered):
            teams[i].participants = [Participant(
                name=p.name,
                participant_id=p.participant_id,
                participant_type=p.participant_type,
                bot_config=p.bot_config
            ) for _ in range(team_size)]
        assign_random_team_names(teams)
        return teams

    num_teams = len(ordered) // team_size

    teams: List[Team] = [
        Team(team_id=_new_team_id(), name=_team_name(i))
        for i in range(num_teams)
    ]

    # Snake draft: 1,2,3,...,N,N,...,3,2,1,1,2,3,...
    direction = 1
    index = 0
    for p in ordered:
        if direction == 1:
            team_idx = index % num_teams
        else:
            team_idx = num_teams - 1 - (index % num_teams)
        teams[team_idx].participants.append(p)
        index += 1
        if index % num_teams == 0:
            direction *= -1

    assign_random_team_names(teams)
    return teams


def form_teams_manual(assignment: List[List[Participant]], team_size: int) -> List[Team]:
    """
    Form teams from an explicit assignment (list of participant lists).
    Each inner list must have exactly team_size participants.
    """
    teams = []
    for i, members in enumerate(assignment):
        if len(members) != team_size:
            raise ValueError(
                f"Team {i + 1} has {len(members)} members, expected {team_size}"
            )
        teams.append(Team(
            team_id=_new_team_id(),
            name=_team_name(i),
            participants=list(members)
        ))
    assign_random_team_names(teams)
    return teams


def _chunk_into_teams(participants: List[Participant], team_size: int) -> List[Team]:
    teams = []
    for i in range(0, len(participants), team_size):
        chunk = participants[i:i + team_size]
        teams.append(Team(
            team_id=_new_team_id(),
            name=_team_name(i // team_size),
            participants=chunk
        ))
    return teams


def _chunk_into_duplicate_teams(participants: List[Participant], team_size: int) -> List[Team]:
    """Each participant is duplicated to form one team (party-mode style)."""
    teams = []
    for i, p in enumerate(participants):
        duped = [Participant(
            name=p.name,
            participant_id=p.participant_id,
            participant_type=p.participant_type,
            bot_config=p.bot_config
        ) for _ in range(team_size)]
        teams.append(Team(
            team_id=_new_team_id(),
            name=_team_name(i),
            participants=duped
        ))
    return teams


def rename_teams(teams: List[Team], names: List[str]) -> None:
    """Apply custom names to teams (names list may be shorter than teams)."""
    for i, team in enumerate(teams):
        if i < len(names) and names[i]:
            team.name = names[i]


def generate_team_names(count: int, exclude_names: Optional[List[str]] = None) -> List[str]:
    """
    Generate ``count`` unique random team names using the descriptor+noun pool.

    Names follow the pattern "<Descriptor> <Noun>" (e.g., "Raging Wolves").
    The pool contains 15 x 15 = 225 combinations, comfortably exceeding the
    100+ requirement.

    Args:
        count: Number of unique names to generate.
        exclude_names: Optional iterable of names that must NOT be reused
            (e.g., names already assigned to other teams, so a re-randomize
            of a single team does not collide with its siblings).

    Returns:
        A list of ``count`` unique name strings.

    Raises:
        ValueError: If ``count`` exceeds the number of available (non-excluded)
            combinations.
    """
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count}")
    if count == 0:
        return []

    excluded = {n.strip().lower() for n in (exclude_names or []) if n and n.strip()}

    # Build the full pool of unique combinations.
    pool = [f"{d} {n}" for d in TEAM_NAME_DESCRIPTORS for n in TEAM_NAME_NOUNS]
    available = [name for name in pool if name.lower() not in excluded]

    if len(available) < count:
        raise ValueError(
            f"Cannot generate {count} unique team names: only {len(available)} "
            f"combinations remain after excluding {len(excluded)} name(s)"
        )

    return random.sample(available, count)


def assign_random_team_names(teams: List[Team]) -> None:
    """
    Assign a unique random name to every team in-place.

    Each team gets a distinct name drawn from the descriptor+noun pool.
    Existing names are excluded from the pool so that re-randomizing the
    whole set never produces a duplicate within the tournament.
    """
    if not teams:
        return
    existing = [t.name for t in teams if t.name and t.name.strip()]
    names = generate_team_names(len(teams), exclude_names=existing)
    for team, name in zip(teams, names):
        team.name = name


def generate_team_bracket(
    teams: List[Team],
    tournament_format: str
) -> Tuple[List[Match], List[Match]]:
    """
    Generate a bracket between teams.

    For team_size == 1 this is equivalent to a participant bracket.
    For team_size > 1, each "participant" slot in the bracket is filled
    with the team's first participant as a stand-in, and the Match's
    team1/team2 fields carry the full team data.

    Returns:
        (matches, losers_bracket_matches)
    """
    if len(teams) < 2:
        return [], []

    # Build stand-in participants (one per team) so the existing
    # bracket generators can be reused unchanged.
    stand_ins = []
    for t in teams:
        stand_in = Participant(
            name=t.name,
            participant_id=t.team_id,
            participant_type='team',
            seed=0
        )
        stand_ins.append(stand_in)

    losers_matches: List[Match] = []

    if tournament_format == 'single_elimination':
        matches, _ = generate_single_elimination_bracket(stand_ins)
    elif tournament_format == 'double_elimination':
        matches, losers_matches, _ = generate_double_elimination_bracket(stand_ins)
    elif tournament_format == 'round_robin':
        matches = generate_round_robin_bracket(stand_ins)
    else:
        raise ValueError(f"Unknown tournament format: {tournament_format}")

    # Attach team data to each match
    team_by_id = {t.team_id: t for t in teams}
    for match in matches:
        _attach_teams(match, team_by_id)
    for match in losers_matches:
        _attach_teams(match, team_by_id)

    return matches, losers_matches


def _attach_teams(match: Match, team_by_id: dict) -> None:
    """Set match.team1/team2 from the stand-in participant ids."""
    if match.participant1 and match.participant1.participant_id in team_by_id:
        match.team1 = team_by_id[match.participant1.participant_id]
    if match.participant2 and match.participant2.participant_id in team_by_id:
        match.team2 = team_by_id[match.participant2.participant_id]
    if match.winner and match.winner.participant_id in team_by_id:
        match.winner_team = team_by_id[match.winner.participant_id]


def build_match_bot_list(match: Match) -> List[dict]:
    """
    Build the bot_list for start_match_helper from a (possibly team-based) match.

    Team 0 members go to slots 0-3, team 1 members to slots 4-7.
    """
    bot_list = []

    def add_participant(p: Participant, team_index: int, slot: int):
        # Always include 'skill' and 'path' so create_player_config() in
        # match_runner.py (which reads bot['skill'] unconditionally) never
        # raises a KeyError. Humans get skill=None (ignored) and no path.
        entry = {
            'name': p.name,
            'team': team_index,
            'slot': slot,
            'skill': None,
            'path': ''
        }
        if p.participant_type == 'human':
            entry['type'] = 'human'
        else:
            entry['type'] = 'rlbot'
            entry['path'] = p.bot_config.get('path', '') if p.bot_config else ''
            entry['skill'] = 10
        bot_list.append(entry)

    if match.team1 is not None and match.team2 is not None:
        for i, p in enumerate(match.team1.participants):
            add_participant(p, 0, i)
        for i, p in enumerate(match.team2.participants):
            add_participant(p, 1, i)
    else:
        # Fallback: 1v1 participant-based match
        if match.participant1:
            add_participant(match.participant1, 0, 0)
        if match.participant2:
            add_participant(match.participant2, 1, 0)

    return bot_list


def team_strength(team: Team) -> float:
    """
    Simple team strength estimate for the balance indicator.
    Bots count as 1.0, humans as 0.5 (unknown skill).
    """
    total = 0.0
    for p in team.participants:
        if p.participant_type == 'bot':
            total += 1.0
        else:
            total += 0.5
    return total


def team_balance_report(teams: List[Team]) -> dict:
    """
    Compute a simple balance report across all teams.
    """
    strengths = {t.team_id: team_strength(t) for t in teams}
    values = list(strengths.values())
    if not values:
        return {'balanced': True, 'spread': 0.0, 'strengths': strengths}
    spread = max(values) - min(values)
    return {
        'balanced': spread <= 1.0,
        'spread': spread,
        'strengths': strengths
    }


def pair_participants(
    participants: List[Participant],
    pairings: List[Tuple[str, str]],
    team_size: int
) -> Tuple[List[List[Participant]], List[str]]:
    """
    Create team assignments based on manual pairings.

    Args:
        participants: Full list of participants.
        pairings: List of (participant_id1, participant_id2) tuples indicating
            which participants must be on the same team.
        team_size: Number of participants per team.

    Returns:
        (assignments, errors) where assignments is a list of participant lists
        (each inner list is a team), and errors contains any error messages.

    The algorithm:
        1. Build a graph of pairings (each edge means two participants must be together).
        2. Find connected components (each component is a group that must stay together).
        3. If any component exceeds team_size, return an error.
        4. Assign each component to a team slot.
        5. Fill remaining slots with unpaired participants.
    """
    errors = []

    # Build participant lookup
    by_id = {p.participant_id: p for p in participants}

    # Build adjacency list for pairings
    from collections import defaultdict
    adj = defaultdict(set)
    for pid1, pid2 in pairings:
        if pid1 not in by_id:
            errors.append(f"Participant '{pid1}' not found in participant pool")
            continue
        if pid2 not in by_id:
            errors.append(f"Participant '{pid2}' not found in participant pool")
            continue
        adj[pid1].add(pid2)
        adj[pid2].add(pid1)

    # Find connected components (groups of participants that must be together)
    visited = set()
    components = []

    def dfs(pid: str) -> List[str]:
        """Return all participant IDs in the same component."""
        stack = [pid]
        component = []
        while stack:
            curr = stack.pop()
            if curr in visited:
                continue
            visited.add(curr)
            component.append(curr)
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    stack.append(neighbor)
        return component

    for pid in by_id:
        if pid not in visited and pid in adj:
            comp = dfs(pid)
            if len(comp) > team_size:
                errors.append(
                    f"Group of {len(comp)} participants exceeds team size ({team_size}). "
                    f"Please reduce pairings or increase team size."
                )
            else:
                components.append(comp)

    # Build assignments from components
    assignments = []
    used = set()

    for comp in components:
        team_members = [by_id[pid] for pid in comp]
        assignments.append(team_members)
        used.update(comp)

    # Add remaining unpaired participants as individual teams (to be filled later)
    remaining = [p for p in participants if p.participant_id not in used]

    return assignments, errors, remaining


def form_teams_with_manual_pairings(
    participants: List[Participant],
    pairings: List[Tuple[str, str]],
    team_size: int,
    allow_duplicates: bool = False
) -> Tuple[List[Team], List[str]]:
    """
    Form teams from participants with manual pairings.

    Args:
        participants: Full list of participants.
        pairings: List of (participant_id1, participant_id2) tuples.
        team_size: Number of participants per team.
        allow_duplicates: If True, each unique participant becomes one team.

    Returns:
        (teams, errors) where teams is the list of formed teams,
        and errors contains any error messages.
    """
    if allow_duplicates:
        # In duplicate mode, pairings don't apply (each participant is one team)
        teams = form_teams_random(participants, team_size, allow_duplicates=True)
        return teams, []

    # Validate team size
    if len(participants) % team_size != 0:
        missing = team_size - (len(participants) % team_size)
        return [], [
            f"Participant count ({len(participants)}) is not divisible by team size "
            f"({team_size}). Add {missing} more participant(s) to form full teams."
        ]

    # Get paired groups and remaining participants
    assignments, errors, remaining = pair_participants(participants, pairings, team_size)

    if errors:
        return [], errors

    # Fill remaining slots with unpaired participants
    # Group remaining into teams of team_size
    remaining_teams = []
    for i in range(0, len(remaining), team_size):
        chunk = remaining[i:i + team_size]
        if len(chunk) == team_size:
            remaining_teams.append(chunk)

    # Combine all assignments
    all_assignments = assignments + remaining_teams

    # Create Team objects
    teams = []
    for i, members in enumerate(all_assignments):
        if len(members) != team_size:
            errors.append(
                f"Team {i + 1} has {len(members)} members, expected {team_size}"
            )
            continue
        teams.append(Team(
            team_id=_new_team_id(),
            name=_team_name(i),
            participants=list(members)
        ))

    if teams:
        assign_random_team_names(teams)

    return teams, errors
