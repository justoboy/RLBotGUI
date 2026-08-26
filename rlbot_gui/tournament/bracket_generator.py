"""
Bracket generation algorithms for tournaments
"""
import math
from typing import List, Tuple, Optional
from rlbot_gui.tournament.tournament_state import Match, Participant


def generate_single_elimination_bracket(participants: List[Participant]) -> Tuple[List[Match], int]:
    """
    Generate a single elimination bracket for the given participants.
    
    Returns:
        Tuple of (list of matches, number of rounds)
    """
    num_participants = len(participants)
    
    # Find the next power of 2
    bracket_size = 1
    while bracket_size < num_participants:
        bracket_size *= 2
    
    num_rounds = int(math.log2(bracket_size))
    
    # Create bye slots if needed
    slots = []
    for p in participants:
        slots.append(p)
    
    # Add bye slots for power of 2
    while len(slots) < bracket_size:
        slots.append(None)  # None represents a bye
    
    # Seed participants using standard bracket seeding
    seeded_slots = seed_bracket(slots, bracket_size)
    
    # Generate matches for round 1
    matches = []
    match_id_counter = 1
    
    # First round matches
    round1_matches = []
    for i in range(0, bracket_size, 2):
        match_id = f"M{match_id_counter}"
        match = Match(
            match_id=match_id,
            round_num=1,
            participant1=seeded_slots[i],
            participant2=seeded_slots[i + 1] if i + 1 < len(seeded_slots) else None,
            completed=False
        )
        # Handle byes - if one participant is None, the other advances automatically
        if match.participant2 is None and match.participant1 is not None:
            match.completed = True
            match.winner = match.participant1
        elif match.participant1 is None and match.participant2 is not None:
            match.completed = True
            match.winner = match.participant2
        
        round1_matches.append(match)
        match_id_counter += 1
    
    # Generate subsequent round matches (placeholders)
    remaining_matches = round1_matches
    round_num = 2
    
    while len(remaining_matches) > 1:
        next_round_matches = []
        for i in range(0, len(remaining_matches), 2):
            match_id = f"M{match_id_counter}"
            match = Match(
                match_id=match_id,
                round_num=round_num,
                participant1=None,
                participant2=None,
                completed=False,
                next_match_id=None
            )
            # Set next_match_id for previous round matches
            if i < len(remaining_matches):
                if i + 1 < len(remaining_matches):
                    remaining_matches[i].next_match_id = match_id
                    remaining_matches[i + 1].next_match_id = match_id
                else:
                    remaining_matches[i].next_match_id = match_id
            
            next_round_matches.append(match)
            match_id_counter += 1
        
        matches.extend(remaining_matches)
        remaining_matches = next_round_matches
        round_num += 1
    
    # Add final round match
    if remaining_matches:
        matches.extend(remaining_matches)
    
    return matches, num_rounds


def seed_bracket(slots: List[Optional[Participant]], bracket_size: int) -> List[Optional[Participant]]:
    """
    Apply standard bracket seeding to ensure top seeds don't meet until later rounds.
    
    Standard seeding pattern for bracket_size=8: [1, 8, 5, 4, 6, 3, 2, 7]
    """
    if len(slots) == 0:
        return slots
    
    # Create a new list for seeded slots
    seeded = [None] * bracket_size
    
    # Get actual participants (non-None slots)
    participants = [s for s in slots if s is not None]
    
    # Sort by seed
    participants.sort(key=lambda p: p.seed)
    
    # Standard seeding positions
    # For each round, we pair seeds that would meet in the final if they keep winning
    if len(participants) == 0:
        return slots
    
    # Simple approach: place participants in bracket order
    # Seed 1 plays the last seed, seed 2 plays second-to-last, etc.
    seed_positions = get_seed_positions(bracket_size)
    
    for i, pos in enumerate(seed_positions):
        if i < len(participants):
            seeded[pos] = participants[i]
    
    return seeded


def get_seed_positions(bracket_size: int) -> List[int]:
    """
    Get the positions in the bracket where seeds should be placed.
    Returns positions in order of seed (position for seed 1, position for seed 2, etc.)
    """
    if bracket_size == 2:
        return [0, 1]
    
    if bracket_size == 4:
        return [0, 3, 1, 2]  # 1v4, 2v3
    
    if bracket_size == 8:
        return [0, 7, 3, 4, 5, 2, 1, 6]  # 1v8, 4v5, 3v6, 2v7
    
    if bracket_size == 16:
        return [0, 15, 7, 8, 11, 4, 3, 12, 13, 2, 6, 9, 10, 5, 1, 14]
    
    # For larger brackets, use recursive approach
    positions = [0, 1]
    size = 2
    
    while size < bracket_size:
        new_positions = []
        for pos in positions:
            new_positions.append(pos * 2)
            new_positions.append(pos * 2 + 1)
        positions = new_positions
        size *= 2
        
        # Reorder to maintain seeding structure
        if size <= bracket_size:
            positions = reorder_seeding(positions, size)
    
    return positions[:bracket_size]


def reorder_seeding(positions: List[int], size: int) -> List[int]:
    """
    Reorder positions to maintain proper seeding structure.
    """
    # This creates the standard bracket where 1 plays size, 2 plays size-1, etc.
    if size == 2:
        return [0, 1]
    
    result = []
    half = size // 2
    
    for i in range(half):
        result.append(i)
        result.append(size - 1 - i)
    
    return result


def generate_double_elimination_bracket(participants: List[Participant]) -> Tuple[List[Match], List[Match], int]:
    """
    Generate a double elimination bracket.
    
    Returns:
        Tuple of (winners bracket matches, losers bracket matches, number of rounds)
    """
    # For MVP, we'll implement a simplified version
    # Full double elimination is complex and will be added in Phase 2
    return generate_single_elimination_bracket(participants), [], int(math.log2(len(participants))) + 1


def generate_round_robin_bracket(participants: List[Participant]) -> List[Match]:
    """
    Generate a round robin bracket where every participant plays every other.
    
    Returns:
        List of matches
    """
    matches = []
    match_id = 1
    
    for i in range(len(participants)):
        for j in range(i + 1, len(participants)):
            match = Match(
                match_id=f"M{match_id}",
                round_num=1,  # All matches are technically in the same "round"
                participant1=participants[i],
                participant2=participants[j],
                completed=False
            )
            matches.append(match)
            match_id += 1
    
    return matches
