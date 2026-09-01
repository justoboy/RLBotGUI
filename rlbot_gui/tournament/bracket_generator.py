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
    
    # Now process bye winners: place them into their next round matches
    # and recursively handle any cascading byes in later rounds
    _process_bye_winners(matches)
    
    return matches, num_rounds


def _process_bye_winners(matches: List[Match]) -> None:
    """
    Process bye winners by placing them into their next round matches.
    This handles both round 1 byes and byes that occur in later rounds
    when there's an odd number of participants advancing.
    """
    # First pass: find all completed bye matches from round 1
    for match in matches:
        if match.completed and match.winner and match.next_match_id:
            # This is a bye match - advance the winner to the next round
            _advance_bye_winner(match, match.winner, matches)


def _advance_bye_winner(match: Match, winner: Participant, all_matches: List[Match]) -> None:
    """
    Advance a bye winner to their next match.
    If the next match only has one slot filled (because the other slot
    also came from a bye), recursively handle that bye too.
    """
    # Find the next match
    next_match = None
    for m in all_matches:
        if m.match_id == match.next_match_id:
            next_match = m
            break
    
    if next_match is None:
        return
    
    # Place winner in the next match
    if next_match.participant1 is None:
        next_match.participant1 = winner
    elif next_match.participant2 is None:
        next_match.participant2 = winner
    else:
        # Both slots are filled - shouldn't happen with byes
        return
    
    # Check if this creates a bye situation in the next round
    # (i.e., the next match has only 1 participant and the other slot
    # feeds from another bye that hasn't been processed yet)
    if next_match.participant1 is not None and next_match.participant2 is None:
        # Check if the other slot that feeds into this match is also a bye
        # We need to find the other match that feeds into next_match
        completed_feeder = _find_completed_unprocessed_feeder(next_match, all_matches)
        if completed_feeder is not None and completed_feeder.winner:
            # The other feeder is also a bye - advance that winner too
            _advance_bye_winner(completed_feeder, completed_feeder.winner, all_matches)
        else:
            # No completed unprocessed feeder - check if there's no other feeder at all
            all_feeders = _get_all_feeders(next_match, all_matches)
            if len(all_feeders) == 0:
                # No other feeder - this is a bye in a later round
                # The single participant advances automatically
                next_match.completed = True
                next_match.winner = next_match.participant1
                if next_match.next_match_id:
                    _advance_bye_winner(next_match, next_match.participant1, all_matches)
    elif next_match.participant1 is None and next_match.participant2 is not None:
        # Same logic, just swapped
        completed_feeder = _find_completed_unprocessed_feeder(next_match, all_matches)
        if completed_feeder is not None and completed_feeder.winner:
            # The other feeder is also a bye - advance that winner too
            _advance_bye_winner(completed_feeder, completed_feeder.winner, all_matches)
        else:
            all_feeders = _get_all_feeders(next_match, all_matches)
            if len(all_feeders) == 0:
                # No other feeder - this is a bye in a later round
                # The single participant advances automatically
                next_match.completed = True
                next_match.winner = next_match.participant2
                if next_match.next_match_id:
                    _advance_bye_winner(next_match, next_match.participant2, all_matches)


def _get_all_feeders(match: Match, all_matches: List[Match]) -> List[Match]:
    """
    Get all matches that feed into the given match.
    """
    feeders = []
    for m in all_matches:
        if m.next_match_id == match.match_id:
            feeders.append(m)
    return feeders


def _find_completed_unprocessed_feeder(match: Match, all_matches: List[Match]) -> Optional[Match]:
    """
    Find a feeder match that is completed (has a winner) but hasn't been processed
    (i.e., the winner hasn't been placed in this match yet).
    """
    feeders = _get_all_feeders(match, all_matches)
    
    for feeder in feeders:
        # Check if feeder is completed with a winner
        if feeder.completed and feeder.winner:
            # Check if this winner is already in the next match
            if match.participant1 != feeder.winner and match.participant2 != feeder.winner:
                # The winner hasn't been placed in this match yet
                return feeder
    
    return None


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
    
    # Process bye winners in the winners bracket
    _process_bye_winners(winners_matches)
    
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


# ---------------------------------------------------------------------------
# Swiss format (Phase 4)
# ---------------------------------------------------------------------------

def calculate_swiss_rounds(num_participants: int) -> int:
    """
    Calculate the number of Swiss rounds as ceil(log2(num_participants)).
    Minimum 1 round. E.g., 2=1, 4=2, 8=3, 16=4.
    """
    if num_participants < 2:
        return 1
    return max(1, int(math.ceil(math.log2(num_participants))))


def generate_swiss_round1(participants: List[Participant]) -> List[Match]:
    """
    Generate round 1 Swiss matches by pairing participants in seed order.
    Pair 1v2, 3v4, 5v6, etc.
    """
    matches = []
    for i in range(0, len(participants) - 1, 2):
        match = Match(
            match_id=f"S1_{i // 2 + 1}",
            round_num=1,
            participant1=participants[i],
            participant2=participants[i + 1],
            completed=False
        )
        matches.append(match)
    return matches


def _swiss_compute_records(
    participants: List[Participant],
    completed_matches: List[Match]
) -> Dict[str, Dict]:
    """
    Compute per-participant records from completed matches.
    Returns a dict keyed by participant_id with wins, losses, goals_for,
    goals_against, goal_difference, played.
    """
    records = {}
    for p in participants:
        records[p.participant_id] = {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'goals_for': 0,
            'goals_against': 0,
            'played': 0
        }

    for m in completed_matches:
        if not m.completed or not m.score:
            continue
        if not m.participant1 or not m.participant2:
            continue
        p1_id = m.participant1.participant_id
        p2_id = m.participant2.participant_id
        if p1_id not in records or p2_id not in records:
            continue
        s1, s2 = m.score

        records[p1_id]['played'] += 1
        records[p2_id]['played'] += 1
        records[p1_id]['goals_for'] += s1
        records[p1_id]['goals_against'] += s2
        records[p2_id]['goals_for'] += s2
        records[p2_id]['goals_against'] += s1

        if s1 > s2:
            records[p1_id]['wins'] += 1
            records[p2_id]['losses'] += 1
        elif s2 > s1:
            records[p2_id]['wins'] += 1
            records[p1_id]['losses'] += 1
        else:
            records[p1_id]['draws'] += 1
            records[p2_id]['draws'] += 1

    for pid in records:
        records[pid]['goal_difference'] = records[pid]['goals_for'] - records[pid]['goals_against']

    return records


def _swiss_sort_key(records: Dict[str, Dict], tiebreakers: List[str]):
    """
    Build a sort key function for Swiss standings.
    Primary: wins (descending).
    Then: user-selected tiebreakers in order.
    Fallback: goal_difference, goals_for.
    """
    def key(p: Participant):
        r = records.get(p.participant_id, {})
        wins = r.get('wins', 0)
        gd = r.get('goal_difference', 0)
        gf = r.get('goals_for', 0)

        # Build tiebreaker tuple in user-specified order
        tb_values = []
        for tb in tiebreakers:
            if tb == 'score_differential':
                tb_values.append(-gd)
            elif tb == 'goals_scored':
                tb_values.append(-gf)
            elif tb == 'head_to_head':
                # Head-to-head is handled separately; use 0 as placeholder
                tb_values.append(0)
            else:
                tb_values.append(0)

        # Fallback tiebreakers
        tb_values.append(-gd)
        tb_values.append(-gf)

        return (-wins,) + tuple(tb_values)

    return key


def generate_swiss_next_round(
    participants: List[Participant],
    completed_matches: List[Match],
    round_num: int,
    tiebreakers: List[str]
) -> List[Match]:
    """
    Generate the next round of Swiss matches based on current records.

    Algorithm:
    1. Compute records (wins, losses, goals) from completed matches.
    2. Sort participants by wins (desc), then by user-selected tiebreakers.
    3. Pair 1st with 2nd, 3rd with 4th, etc.
    4. Avoid rematches when possible (swap with next available non-rematch opponent).

    Args:
        participants: All participants in the tournament.
        completed_matches: All completed matches so far.
        round_num: The round number to generate (2, 3, ...).
        tiebreakers: Ordered list of tiebreaker keys.

    Returns:
        List of Match objects for the new round.
    """
    if len(participants) < 2:
        return []

    records = _swiss_compute_records(participants, completed_matches)
    sort_key = _swiss_sort_key(records, tiebreakers)
    sorted_participants = sorted(participants, key=sort_key)

    # Track previous opponents to avoid rematches
    previous_opponents: Dict[str, set] = {}
    for m in completed_matches:
        if m.participant1 and m.participant2:
            p1_id = m.participant1.participant_id
            p2_id = m.participant2.participant_id
            previous_opponents.setdefault(p1_id, set()).add(p2_id)
            previous_opponents.setdefault(p2_id, set()).add(p1_id)

    # Greedy pairing: take the highest-ranked remaining participant and pair
    # them with the highest-ranked opponent they have not played yet.
    # If every remaining opponent is a rematch (pool exhausted in late
    # rounds), allow the rematch as a fallback.
    remaining = list(sorted_participants)
    matches = []
    match_num = 1

    while len(remaining) >= 2:
        p1 = remaining.pop(0)
        p1_prev = previous_opponents.get(p1.participant_id, set())

        opponent = None
        for candidate in remaining:
            if candidate.participant_id not in p1_prev:
                opponent = candidate
                break
        if opponent is None:
            opponent = remaining[0]  # All opponents are rematches; allow it

        remaining.remove(opponent)

        match = Match(
            match_id=f"S{round_num}_{match_num}",
            round_num=round_num,
            participant1=p1,
            participant2=opponent,
            completed=False
        )
        matches.append(match)
        match_num += 1

    return matches


def calculate_swiss_standings(
    participants: List[Participant],
    completed_matches: List[Match],
    tiebreakers: List[str]
) -> List[Dict]:
    """
    Calculate Swiss standings with user-selectable tiebreakers.

    Returns:
        List of standings dicts sorted by wins (desc), then tiebreakers.
        Each dict has: participant, wins, losses, draws, goals_for,
        goals_against, goal_difference, played, rank.
    """
    records = _swiss_compute_records(participants, completed_matches)
    sort_key = _swiss_sort_key(records, tiebreakers)
    sorted_participants = sorted(participants, key=sort_key)

    standings = []
    for rank, p in enumerate(sorted_participants, 1):
        r = records.get(p.participant_id, {})
        standings.append({
            'participant': p,
            'rank': rank,
            'wins': r.get('wins', 0),
            'losses': r.get('losses', 0),
            'draws': r.get('draws', 0),
            'goals_for': r.get('goals_for', 0),
            'goals_against': r.get('goals_against', 0),
            'goal_difference': r.get('goal_difference', 0),
            'played': r.get('played', 0)
        })

    return standings


def _swiss_head_to_head(
    p1: Participant,
    p2: Participant,
    completed_matches: List[Match]
) -> Optional[Participant]:
    """
    Return the winner of the head-to-head match between p1 and p2,
    or None if they have not played each other or the match was a draw.
    """
    for m in completed_matches:
        if not m.completed or not m.score:
            continue
        if not m.participant1 or not m.participant2:
            continue
        ids = {m.participant1.participant_id, m.participant2.participant_id}
        if p1.participant_id in ids and p2.participant_id in ids:
            s1, s2 = m.score
            if s1 > s2:
                return m.participant1
            elif s2 > s1:
                return m.participant2
            # Draw: no head-to-head winner
            return None
    return None


def determine_swiss_winner(
    participants: List[Participant],
    completed_matches: List[Match],
    tiebreakers: List[str]
) -> Dict:
    """
    Determine the Swiss tournament winner.

    Winner determination:
    1. Most wins after all rounds.
    2. If the top 2 are tied on wins, apply the user-selected tiebreakers
       in priority order to separate them:
         - score_differential: higher goal difference wins
         - goals_scored: higher total goals wins
         - head_to_head: winner of their direct match wins
    3. If the tiebreakers cannot separate the top 2, a head-to-head
       playoff match is required.

    Returns:
        Dict with:
          - 'winner': the winning Participant (or None if playoff needed)
          - 'playoff_needed': True if top 2 are tied and need a playoff
          - 'playoff_participants': [p1, p2] if playoff needed
          - 'standings': full standings list
    """
    standings = calculate_swiss_standings(participants, completed_matches, tiebreakers)

    if len(standings) < 2:
        return {
            'winner': standings[0]['participant'] if standings else None,
            'playoff_needed': False,
            'playoff_participants': [],
            'standings': standings
        }

    top = standings[0]
    second = standings[1]

    # If top 2 have different win counts, the top is the winner.
    if top['wins'] != second['wins']:
        return {
            'winner': top['participant'],
            'playoff_needed': False,
            'playoff_participants': [],
            'standings': standings
        }

    # Top 2 are tied on wins. Apply tiebreakers in user-specified order.
    p1 = top['participant']
    p2 = second['participant']

    for tb in tiebreakers:
        if tb == 'score_differential':
            if top['goal_difference'] != second['goal_difference']:
                winner = p1 if top['goal_difference'] > second['goal_difference'] else p2
                return {
                    'winner': winner,
                    'playoff_needed': False,
                    'playoff_participants': [],
                    'standings': standings
                }
        elif tb == 'goals_scored':
            if top['goals_for'] != second['goals_for']:
                winner = p1 if top['goals_for'] > second['goals_for'] else p2
                return {
                    'winner': winner,
                    'playoff_needed': False,
                    'playoff_participants': [],
                    'standings': standings
                }
        elif tb == 'head_to_head':
            h2h = _swiss_head_to_head(p1, p2, completed_matches)
            if h2h is not None:
                return {
                    'winner': h2h,
                    'playoff_needed': False,
                    'playoff_participants': [],
                    'standings': standings
                }

    # Tiebreakers could not separate the top 2. A playoff is required.
    return {
        'winner': None,
        'playoff_needed': True,
        'playoff_participants': [p1, p2],
        'standings': standings
    }


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
