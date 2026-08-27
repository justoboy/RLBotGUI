"""
Bracket generation algorithms for tournaments
"""
import math
from typing import List, Tuple, Optional, Dict
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
    num_participants = len(participants)
    
    if num_participants < 2:
        return [], [], 0
    
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
        slots.append(None)
    
    # Seed participants
    seeded_slots = seed_bracket(slots, bracket_size)
    
    # Generate winners bracket (same as single elimination)
    winners_matches = []
    match_id_counter = 1
    
    # First round winners bracket matches
    round1_matches = []
    for i in range(0, bracket_size, 2):
        match_id = f"W{match_id_counter}"
        match = Match(
            match_id=match_id,
            round_num=1,
            participant1=seeded_slots[i],
            participant2=seeded_slots[i + 1] if i + 1 < len(seeded_slots) else None,
            completed=False
        )
        # Handle byes
        if match.participant2 is None and match.participant1 is not None:
            match.completed = True
            match.winner = match.participant1
        elif match.participant1 is None and match.participant2 is not None:
            match.completed = True
            match.winner = match.participant2
        
        round1_matches.append(match)
        match_id_counter += 1
    
    # Generate subsequent winners bracket rounds
    remaining_matches = round1_matches
    round_num = 2
    
    while len(remaining_matches) > 1:
        next_round_matches = []
        for i in range(0, len(remaining_matches), 2):
            match_id = f"W{match_id_counter}"
            match = Match(
                match_id=match_id,
                round_num=round_num,
                participant1=None,
                participant2=None,
                completed=False,
                next_match_id=None
            )
            if i < len(remaining_matches):
                if i + 1 < len(remaining_matches):
                    remaining_matches[i].next_match_id = match_id
                    remaining_matches[i + 1].next_match_id = match_id
                else:
                    remaining_matches[i].next_match_id = match_id
            
            next_round_matches.append(match)
            match_id_counter += 1
        
        winners_matches.extend(remaining_matches)
        remaining_matches = next_round_matches
        round_num += 1
    
    if remaining_matches:
        winners_matches.extend(remaining_matches)
    
    # Generate losers bracket matches
    losers_matches = []
    
    # Losers bracket structure:
    # - Losers from WB round 1 go to L1
    # - Losers from WB round 2 go to L2, play winners from L1
    # - Continue until losers bracket final
    # - LB winner plays WB winner in grand final
    
    # Round 1 losers (half of bracket_size / 2 matches)
    lb_match_id = 1
    num_lb_rounds = num_rounds - 1 if num_rounds > 1 else 1
    
    # Create losers bracket round 1 (from WB round 1 losers)
    lb_round1_matches = []
    for i in range(0, bracket_size, 4):
        # These are the losers from pairs that feed into WB round 2
        match_id = f"L{lb_match_id}"
        # Match between loser of WB match at position i and i+2
        match = Match(
            match_id=match_id,
            round_num=1,
            participant1=None,  # Will be filled when WB matches complete
            participant2=None,
            completed=False,
            next_match_id=None
        )
        lb_round1_matches.append(match)
        lb_match_id += 1
    
    # Build subsequent losers bracket rounds
    lb_remaining = lb_round1_matches
    lb_round = 2
    
    # Track which WB round feeds into which LB round
    # LB round N receives losers from WB round N+1
    for wb_round in range(2, num_rounds + 1):
        if lb_remaining:
            next_lb_round = []
            num_matches = len(lb_remaining)
            
            for i in range(0, num_matches, 2):
                match_id = f"L{lb_match_id}"
                match = Match(
                    match_id=match_id,
                    round_num=lb_round,
                    participant1=None,
                    participant2=None,
                    completed=False,
                    next_match_id=None
                )
                
                # Link previous round matches
                if i < len(lb_remaining):
                    if i + 1 < len(lb_remaining):
                        lb_remaining[i].next_match_id = match_id
                        lb_remaining[i + 1].next_match_id = match_id
                    else:
                        lb_remaining[i].next_match_id = match_id
                
                next_lb_round.append(match)
                lb_match_id += 1
            
            losers_matches.extend(lb_remaining)
            lb_remaining = next_lb_round
            lb_round += 1
    
    if lb_remaining:
        losers_matches.extend(lb_remaining)
    
    # Link losers bracket matches to winners bracket matches
    # Loser of WB round N goes to LB round N-1 (or LB round 1 if N=1)
    link_losers_to_winners(winners_matches, losers_matches, bracket_size)
    
    # Set losers_next_match_id for winners bracket matches
    set_winners_bracket_loser_destinations(winners_matches, losers_matches)
    
    return winners_matches, losers_matches, num_rounds


def link_losers_to_winners(winners_matches: List[Match], losers_matches: List[Match], bracket_size: int):
    """
    Link losers bracket matches to their corresponding winners bracket matches.
    When a WB match loses, they advance to their LB match.
    """
    # Group WB matches by round
    wb_by_round = {}
    for m in winners_matches:
        if m.round_num not in wb_by_round:
            wb_by_round[m.round_num] = []
        wb_by_round[m.round_num].append(m)
    
    # Group LB matches by round
    lb_by_round = {}
    for m in losers_matches:
        if m.round_num not in lb_by_round:
            lb_by_round[m.round_num] = []
        lb_by_round[m.round_num].append(m)
    
    # Link: loser of WB round N goes to LB round N (for N > 1)
    # Loser of WB round 1 goes to LB round 1
    for wb_round, wb_matches in wb_by_round.items():
        lb_round = wb_round  # Loser of WB round N goes to LB round N
        if lb_round in lb_by_round:
            lb_matches = lb_by_round[lb_round]
            # Each WB match's loser goes to an LB match
            for i, wb_match in enumerate(wb_matches):
                if i < len(lb_matches):
                    wb_match.loser_next_match_id = lb_matches[i].match_id


def set_winners_bracket_loser_destinations(winners_matches: List[Match], losers_matches: List[Match]):
    """
    Set the loser_next_match_id for winners bracket matches.
    """
    # Group matches by round
    wb_by_round = {}
    for m in winners_matches:
        if m.round_num not in wb_by_round:
            wb_by_round[m.round_num] = []
        wb_by_round[m.round_num].append(m)
    
    lb_by_round = {}
    for m in losers_matches:
        if m.round_num not in lb_by_round:
            lb_by_round[m.round_num] = []
        lb_by_round[m.round_num].append(m)
    
    # For each WB round, set loser destinations
    for wb_round, wb_matches in wb_by_round.items():
        # Loser of WB round N typically goes to LB round N
        if wb_round in lb_by_round:
            lb_matches = lb_by_round[wb_round]
            for i, wb_match in enumerate(wb_matches):
                if i < len(lb_matches):
                    wb_match.loser_next_match_id = lb_matches[i].match_id


def generate_round_robin_bracket(participants: List[Participant]) -> List[Match]:
    """
    Generate a round robin bracket where every participant plays every other.
    
    Uses circle method for scheduling:
    - For even N: N-1 rounds, each participant plays once per round
    - For odd N: N rounds, one participant sits out each round
    
    Returns:
        List of matches with proper round assignments
    """
    matches = []
    match_id = 1
    
    num_participants = len(participants)
    
    if num_participants < 2:
        return matches
    
    # Create round-robin schedule using circle method
    # For N participants:
    # - If N is even: N-1 rounds, each round has N/2 matches
    # - If N is odd: N rounds, each round has (N-1)/2 matches (one bye per round)
    
    # Create a list of participant indices
    indices = list(range(num_participants))
    
    # Determine number of rounds
    if num_participants % 2 == 0:
        num_rounds = num_participants - 1
        participants_per_round = num_participants // 2
    else:
        num_rounds = num_participants
        participants_per_round = num_participants // 2
    
    # Generate matches for each round using circle method
    for round_num in range(1, num_rounds + 1):
        round_matches = []
        
        # Fix first participant, rotate others
        # For circle method: index 0 stays fixed, others rotate
        rotated_indices = [indices[0]]
        for i in range(1, num_participants):
            # Rotate: position i gets value from position (i - round_num) mod (N-1)
            rotated_idx = 1 + ((i - round_num) % (num_participants - 1)) if num_participants > 2 else 1
            rotated_indices.append(indices[rotated_idx])
        
        # Create matches: first vs last, second vs second-to-last, etc.
        for i in range(participants_per_round):
            p1_idx = rotated_indices[i]
            p2_idx = rotated_indices[num_participants - 1 - i]
            
            # Skip if same participant (bye)
            if p1_idx == p2_idx:
                continue
            
            match = Match(
                match_id=f"M{match_id}",
                round_num=round_num,
                participant1=participants[p1_idx],
                participant2=participants[p2_idx],
                completed=False
            )
            round_matches.append(match)
            match_id += 1
        
        matches.extend(round_matches)
    
    return matches


def calculate_round_robin_standings(matches: List[Match], participants: List[Participant]) -> List[Dict]:
    """
    Calculate standings for a round robin tournament.
    
    Scoring:
    - Win: 3 points
    - Draw: 1 point
    - Loss: 0 points
    
    Returns:
        List of standings sorted by points (descending), then goal difference, then goals scored
    """
    standings = {}
    
    # Initialize standings for all participants
    for p in participants:
        standings[p.participant_id] = {
            'participant': p,
            'played': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_for': 0,
            'goals_against': 0,
            'goal_difference': 0,
            'points': 0
        }
    
    # Process completed matches
    for match in matches:
        if not match.completed or match.score is None:
            continue
        
        if match.participant1 is None or match.participant2 is None:
            continue
        
        p1_id = match.participant1.participant_id
        p2_id = match.participant2.participant_id
        score1, score2 = match.score
        
        # Update games played
        standings[p1_id]['played'] += 1
        standings[p2_id]['played'] += 1
        
        # Update goals
        standings[p1_id]['goals_for'] += score1
        standings[p1_id]['goals_against'] += score2
        standings[p2_id]['goals_for'] += score2
        standings[p2_id]['goals_against'] += score1
        
        # Determine winner/draw
        if score1 > score2:
            # Player 1 wins
            standings[p1_id]['wins'] += 1
            standings[p1_id]['points'] += 3
            standings[p2_id]['losses'] += 1
        elif score2 > score1:
            # Player 2 wins
            standings[p2_id]['wins'] += 1
            standings[p2_id]['points'] += 3
            standings[p1_id]['losses'] += 1
        else:
            # Draw
            standings[p1_id]['draws'] += 1
            standings[p1_id]['points'] += 1
            standings[p2_id]['draws'] += 1
            standings[p2_id]['points'] += 1
    
    # Calculate goal difference
    for p_id in standings:
        standings[p_id]['goal_difference'] = (
            standings[p_id]['goals_for'] - standings[p_id]['goals_against']
        )
    
    # Convert to list and sort
    result = list(standings.values())
    result.sort(key=lambda x: (x['points'], x['goal_difference'], x['goals_for']), reverse=True)
    
    return result
