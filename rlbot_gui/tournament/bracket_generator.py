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
    
    Uses multiple passes to handle cascading byes (e.g., a bye winner advancing
    to a match where the opponent is also a bye winner).
    """
    # Keep processing until no more bye winners can be advanced
    changed = True
    max_iterations = len(matches) * 2  # Safety limit to prevent infinite loops
    iteration = 0
    
    while changed and iteration < max_iterations:
        iteration += 1
        changed = False
        for match in matches:
            if match.completed and match.winner and match.next_match_id:
                # Check if this winner has already been placed in the next match
                next_match = None
                for m in matches:
                    if m.match_id == match.next_match_id:
                        next_match = m
                        break
                
                if next_match is None:
                    continue
                
                # Check if the winner is already in the next match
                already_placed = (next_match.participant1 == match.winner or 
                                next_match.participant2 == match.winner)
                
                if not already_placed:
                    # This is a bye match - advance the winner to the next round
                    _advance_bye_winner(match, match.winner, matches)
                    changed = True
                # else: Winner is already in the next match, nothing to do


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
        # Both slots are filled - check if winner is already in the match
        if next_match.participant1 != winner and next_match.participant2 != winner:
            # Winner is not in the match, but both slots are filled - this is an error
            return
        # Winner is already in the match, nothing to do
        return
    
    # Do NOT auto-complete matches here. Let the actual gameplay handle match completion.
    # This prevents matches from being auto-advanced when both participants are present
    # but haven't actually played yet.
    
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
    This includes both winner feeders (next_match_id) and loser feeders (loser_next_match_id).
    For LB matches, WB losers are linked via loser_next_match_id.
    """
    feeders = []
    for m in all_matches:
        if m.next_match_id == match.match_id or m.loser_next_match_id == match.match_id:
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


def generate_double_elimination_bracket(participants: List[Participant]) -> Tuple[List[Match], List[Match], Optional[Match], int]:
    """
    Generate a double elimination bracket.
    
    Returns:
        Tuple of (winners bracket matches, losers bracket matches, grand final match, number of rounds)
        grand final match is None if the tournament has fewer than 2 participants
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
    wb_round = 2
    
    while len(remaining_matches) > 1:
        next_round_matches = []
        
        for i in range(0, len(remaining_matches), 2):
            match_id = f"W{match_id_counter}"
            match = Match(
                match_id=match_id,
                round_num=wb_round,
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
        wb_round += 1
    
    if remaining_matches:
        winners_matches.extend(remaining_matches)
    
    # Process bye winners in the winners bracket FIRST
    # This ensures that subsequent rounds have the correct participants
    _process_bye_winners(winners_matches)
    
    # Generate losers bracket matches
    # 
    # Standard double elimination structure for bracket_size participants:
    # For 8 players (num_rounds=3):
    # - LB Round 1: 2 matches (losers from WB Round 1 paired)
    # - LB Round 2: 2 matches (winners from LB R1 + losers from WB R2)
    # - LB Round 3: 1 match (winners from LB R2 play each other)
    # - LB Round 4 (LB Finals): 1 match (winner from LB R3 + loser from WB Finals)
    # - Grand Final: 1 match (WB winner vs LB winner)
    #
    # Number of LB rounds (excluding Grand Final) = 2 * num_rounds - 2
    # For 8 players: 2*3 - 2 = 4 LB rounds
    # For 16 players: 2*4 - 2 = 6 LB rounds
    #
    # LB Round structure:
    # - Odd-numbered LB rounds (1, 3, 5, ...): winners from previous LB round play each other
    # - Even-numbered LB rounds (2, 4, 6, ...): winners from previous LB round + losers from WB Round (N/2 + 1)
    
    # Calculate the actual number of losers from each WB round
    # This is needed to size LB rounds correctly for non-power-of-2 participant counts
    # NOTE: This is calculated AFTER _process_bye_winners to account for bye winners
    
    # Group WB matches by round first
    wb_by_round_calc: Dict[int, List[Match]] = {}
    for m in winners_matches:
        if m.round_num not in wb_by_round_calc:
            wb_by_round_calc[m.round_num] = []
        wb_by_round_calc[m.round_num].append(m)
    
    wb_losers_by_round: Dict[int, int] = {}
    for wb_round_num, matches in wb_by_round_calc.items():
        wb_losers_by_round[wb_round_num] = 0
        if wb_round_num == 1:
            # For WB R1: count matches with both participants (actual matches)
            for m in matches:
                if m.participant1 is not None and m.participant2 is not None:
                    wb_losers_by_round[wb_round_num] += 1
        else:
            # For subsequent WB rounds: ALL matches will produce losers during simulation
            # because any "missing" participants come from unresolved byes (winners of previous round matches)
            # So count ALL matches in this round as producing losers, not just those with both participants
            wb_losers_by_round[wb_round_num] = len(matches)
    
    print(f"=== DEBUG: WB losers by round: {wb_losers_by_round} ===")
    
    losers_matches = []
    lb_by_round: Dict[int, List[Match]] = {}
    lb_match_id = 1
    
    # Calculate total number of LB rounds (excluding Grand Final)
    num_lb_rounds = 2 * num_rounds - 2
    
    print(f"=== DEBUG: Generating Losers Bracket for {num_participants} participants ===")
    print(f"=== bracket_size={bracket_size}, num_rounds={num_rounds}, num_lb_rounds={num_lb_rounds} ===")
    
    # Create LB rounds using actual losers count (not bracket_size)
    # This ensures the LB structure matches the actual flow of the tournament
    for lb_round_num in range(1, num_lb_rounds + 1):
        if lb_round_num == 1:
            # LB R1: participants are losers from WB R1
            # Number of matches = ceil(losers_from_wb_r1 / 2)
            losers_from_wb_r1 = wb_losers_by_round.get(1, 0)
            num_lb_matches = math.ceil(losers_from_wb_r1 / 2) if losers_from_wb_r1 > 0 else 0
        elif lb_round_num % 2 == 1:
            # Odd round (3, 5, ...): winners from previous LB round play each other
            # Number of matches = ceil(prev_round_matches / 2)
            prev_round_matches = len(lb_by_round.get(lb_round_num - 1, []))
            num_lb_matches = math.ceil(prev_round_matches / 2) if prev_round_matches > 0 else 0
        else:
            # Even round (2, 4, 6, ...): winners from previous LB round + losers from WB round
            # Total participants = prev_round_matches (winners) + losers_from_wb
            # Number of matches = ceil(total_participants / 2)
            prev_round_matches = len(lb_by_round.get(lb_round_num - 1, []))
            
            # Calculate losers from corresponding WB round
            # LB R2 gets losers from WB R2, LB R4 gets losers from WB R3, etc.
            # Formula: WB round = (LB round / 2) + 1
            wb_round_for_losers = (lb_round_num // 2) + 1
            losers_from_wb = wb_losers_by_round.get(wb_round_for_losers, 0)
            
            # Total participants in this round (includes bye winners from previous round)
            total_participants = prev_round_matches + losers_from_wb
            num_lb_matches = math.ceil(total_participants / 2) if total_participants > 0 else 0
        
        # Ensure at least 1 match if there are any participants (including bye winners)
        # This handles the case where prev_round had 1 match (bye winner advances)
        if num_lb_matches < 1 and (lb_round_num == 1 or len(lb_by_round.get(lb_round_num - 1, [])) > 0 or wb_losers_by_round.get((lb_round_num // 2) + 1, 0) > 0):
            num_lb_matches = 1
        
        print(f"=== LB Round {lb_round_num}: {num_lb_matches} matches ===")
        
        lb_round_matches = []
        for i in range(num_lb_matches):
            match_id = f"L{lb_match_id}"
            match = Match(
                match_id=match_id,
                round_num=lb_round_num,
                participant1=None,
                participant2=None,
                completed=False,
                next_match_id=None
            )
            lb_round_matches.append(match)
            print(f"===   Created {match_id} ===")
            lb_match_id += 1
        
        lb_by_round[lb_round_num] = lb_round_matches
        losers_matches.extend(lb_round_matches)
    
    # Handle edge case: if num_lb_rounds <= 0, there's no Losers Bracket
    # This happens when there's only 1 WB round (2 participants)
    if num_lb_rounds <= 0:
        print(f"=== DEBUG: No Losers Bracket needed (num_lb_rounds={num_lb_rounds}) ===")
        # For 2 participants, the WB final IS the tournament final
        # Return the WB matches without Losers Bracket or Grand Final
        return winners_matches, [], None, num_rounds
    
    # Create Grand Final match
    # Grand Final round number: num_lb_rounds + 1 (comes after LB Finals)
    grand_final_id = f"L{lb_match_id}"
    grand_final_round_num = num_lb_rounds + 1
    grand_final_match = Match(
        match_id=grand_final_id,
        round_num=grand_final_round_num,
        participant1=None,  # WB winner
        participant2=None,  # LB winner (from LB Finals)
        completed=False,
        next_match_id=None
    )
    # Note: Grand Final is NOT added to losers_matches
    # It will be returned separately and added to the main matches array
    # losers_matches.append(grand_final_match)
    
    # Get LB Finals match (last LB round)
    lb_finals_round = num_lb_rounds
    lb_finals_id = None
    lb_finals_match = None
    if lb_finals_round in lb_by_round and len(lb_by_round[lb_finals_round]) > 0:
        lb_finals_match = lb_by_round[lb_finals_round][0]
        lb_finals_id = lb_finals_match.match_id
        print(f"=== DEBUG: LB Finals is {lb_finals_id} ===")
    else:
        print(f"=== DEBUG: No LB Finals match (LB round {lb_finals_round} is empty) ===")
    
    # Link LB matches to determine progression
    # Standard double elimination structure:
    # - LB Odd rounds: winners advance one-to-one to next even round
    # - LB Even rounds: winners are paired in next odd round
    # - LB Finals winner advances to Grand Final
    
    print(f"=== DEBUG: Linking LB internal matches ===")
    
    # Link LB Round 1 matches to LB Round 2 matches
    # Each LB Round 1 match's winner goes to a corresponding LB Round 2 match
    if 1 in lb_by_round and 2 in lb_by_round:
        lb_round1_matches = lb_by_round[1]
        lb_round2_matches = lb_by_round[2]
        print(f"=== DEBUG: LB R1 -> LB R2: {len(lb_round1_matches)} matches -> {len(lb_round2_matches)} matches ===")
        for i, lb_match in enumerate(lb_round1_matches):
            if i < len(lb_round2_matches):
                lb_match.next_match_id = lb_round2_matches[i].match_id
                print(f"===   {lb_match.match_id}.winner -> {lb_round2_matches[i].match_id} ===")
    
    # Link LB Round 2+ matches to subsequent rounds
    for lb_round_num in range(2, num_lb_rounds):
        lb_round_matches = lb_by_round[lb_round_num]
        next_lb_round_num = lb_round_num + 1
        next_lb_round_matches = lb_by_round.get(next_lb_round_num, [])
        
        if len(lb_round_matches) == 1:
            # Single match: winner advances to next round
            if next_lb_round_matches:
                lb_round_matches[0].next_match_id = next_lb_round_matches[0].match_id
                print(f"=== DEBUG: LB R{lb_round_num} {lb_round_matches[0].match_id}.winner -> LB R{next_lb_round_num} {next_lb_round_matches[0].match_id} ===")
        else:
            # Multiple matches: winners advance to next round
            # For odd rounds (1, 3, 5, ...): winners advance one-to-one to next round (even round)
            # For even rounds (2, 4, 6, ...): pair winners to next round (odd round)
            if lb_round_num % 2 == 1:
                # Odd round: winners advance one-to-one to next round (even round)
                print(f"=== DEBUG: LB R{lb_round_num} (odd) -> LB R{next_lb_round_num} (even): {len(lb_round_matches)} matches -> {len(next_lb_round_matches)} matches (one-to-one) ===")
                for i, lb_match in enumerate(lb_round_matches):
                    if i < len(next_lb_round_matches):
                        lb_match.next_match_id = next_lb_round_matches[i].match_id
                        print(f"===   {lb_match.match_id}.winner -> {next_lb_round_matches[i].match_id} ===")
            else:
                # Even round: pair consecutive matches, winners play each other in next odd round
                print(f"=== DEBUG: LB R{lb_round_num} (even) -> LB R{next_lb_round_num} (odd): {len(lb_round_matches)} matches -> {len(next_lb_round_matches)} matches (paired) ===")
                for i in range(0, len(lb_round_matches), 2):
                    if i + 1 < len(lb_round_matches):
                        next_match_idx = i // 2
                        if next_match_idx < len(next_lb_round_matches):
                            lb_round_matches[i].next_match_id = next_lb_round_matches[next_match_idx].match_id
                            lb_round_matches[i+1].next_match_id = next_lb_round_matches[next_match_idx].match_id
                            print(f"===   {lb_round_matches[i].match_id}.winner + {lb_round_matches[i+1].match_id}.winner -> {next_lb_round_matches[next_match_idx].match_id} ===")
                    elif i < len(lb_round_matches):
                        # Odd number of matches: last match's winner advances
                        next_match_idx = i // 2
                        if next_match_idx < len(next_lb_round_matches):
                            lb_round_matches[i].next_match_id = next_lb_round_matches[next_match_idx].match_id
                            print(f"===   {lb_round_matches[i].match_id}.winner -> {next_lb_round_matches[next_match_idx].match_id} ===")
    
    # Link LB Finals winner to Grand Final
    lb_finals_match.next_match_id = grand_final_id
    
    # Link WB losers to LB matches
    # Group WB matches by round
    wb_by_round: Dict[int, List[Match]] = {}
    for m in winners_matches:
        if m.round_num not in wb_by_round:
            wb_by_round[m.round_num] = []
        wb_by_round[m.round_num].append(m)
    
    print(f"=== DEBUG: WB rounds: {list(wb_by_round.keys())} ===")
    for rnd, matches in wb_by_round.items():
        print(f"===   WB Round {rnd}: {len(matches)} matches ===")
    
    # Link losers from WB Round 1 to LB Round 1
    # Only link matches that have both participants (will produce losers)
    if 1 in wb_by_round and 1 in lb_by_round:
        wb_round1_matches = wb_by_round[1]
        lb_round1_matches = lb_by_round[1]
        
        # Filter to only matches with both participants (actual matches, not byes)
        actual_wb_r1_matches = [m for m in wb_round1_matches 
                                if m.participant1 is not None and m.participant2 is not None]
        
        print(f"=== DEBUG: Linking WB R1 losers to LB R1: {len(actual_wb_r1_matches)} actual WB matches -> {len(lb_round1_matches)} LB matches ===")
        
        # Pair losers: loser of WB match 0 and 1 go to LB match 0, etc.
        for i, lb_match in enumerate(lb_round1_matches):
            wb_match_idx1 = i * 2
            wb_match_idx2 = i * 2 + 1
            if wb_match_idx1 < len(actual_wb_r1_matches):
                actual_wb_r1_matches[wb_match_idx1].loser_next_match_id = lb_match.match_id
                print(f"===   {actual_wb_r1_matches[wb_match_idx1].match_id}.loser -> {lb_match.match_id} ===")
            if wb_match_idx2 < len(actual_wb_r1_matches):
                actual_wb_r1_matches[wb_match_idx2].loser_next_match_id = lb_match.match_id
                print(f"===   {actual_wb_r1_matches[wb_match_idx2].match_id}.loser -> {lb_match.match_id} ===")
    
    # Link losers from WB Round N (N >= 2, N < num_rounds) to LB Round (2*N - 2)
    # These losers play against winners from LB Round (2*N - 3)
    # During generation, some matches may have bye winners that appear as None until simulation time.
    # So we use ALL matches in the round, not just those with both participants.
    for wb_round in range(2, num_rounds):
        if wb_round in wb_by_round:
            wb_matches = wb_by_round[wb_round]
            # Use all WB matches in this round (including those with bye winners)
            actual_wb_matches = list(wb_matches)
            
            # WB Round N feeds into LB Round (2*N - 2) for N >= 2
            # For N=2: LB Round 2
            # For N=3: LB Round 4
            # For N=4: LB Round 6
            lb_round_num = 2 * wb_round - 2
            if lb_round_num in lb_by_round:
                lb_matches = lb_by_round[lb_round_num]
                prev_lb_round = lb_round_num - 1
                prev_lb_matches = lb_by_round.get(prev_lb_round, [])
                
                print(f"=== DEBUG: Linking WB R{wb_round} losers to LB R{lb_round_num}: {len(actual_wb_matches)} actual WB matches -> {len(lb_matches)} LB matches (prev LB R{prev_lb_round} has {len(prev_lb_matches)} matches) ===")
                
                lb_match_idx = 0
                wb_match_idx = 0
                
                # First pass: pair LB previous round winners with WB losers
                # Each LB match needs one participant from prev LB round (winner) and one from WB (loser)
                for i, prev_lb_match in enumerate(prev_lb_matches):
                    if wb_match_idx < len(actual_wb_matches) and lb_match_idx < len(lb_matches):
                        actual_wb_matches[wb_match_idx].loser_next_match_id = lb_matches[lb_match_idx].match_id
                        print(f"===   {actual_wb_matches[wb_match_idx].match_id}.loser -> {lb_matches[lb_match_idx].match_id} (paired with LB R{prev_lb_round} winner) ===")
                        wb_match_idx += 1
                        lb_match_idx += 1
                
                # Second pass: pair remaining WB losers with each other
                # Each LB match gets 2 WB losers
                while wb_match_idx < len(actual_wb_matches):
                    if lb_match_idx < len(lb_matches):
                        # First WB loser for this match
                        actual_wb_matches[wb_match_idx].loser_next_match_id = lb_matches[lb_match_idx].match_id
                        print(f"===   {actual_wb_matches[wb_match_idx].match_id}.loser -> {lb_matches[lb_match_idx].match_id} ===")
                        wb_match_idx += 1
                        
                        # Second WB loser for this match (if available)
                        if wb_match_idx < len(actual_wb_matches):
                            actual_wb_matches[wb_match_idx].loser_next_match_id = lb_matches[lb_match_idx].match_id
                            print(f"===   {actual_wb_matches[wb_match_idx].match_id}.loser -> {lb_matches[lb_match_idx].match_id} ===")
                            wb_match_idx += 1
                        
                        lb_match_idx += 1
                    else:
                        # No more LB matches - this shouldn't happen with correct formula
                        print(f"===   WARNING: {actual_wb_matches[wb_match_idx].match_id} has no corresponding LB match! ===")
                        wb_match_idx += 1
            else:
                print(f"=== WARNING: LB Round {lb_round_num} does not exist for WB Round {wb_round}! ===")
    
    # Link loser from WB Finals to LB Finals (if LB Finals exists)
    # Find the final WB match (the one with no next_match_id)
    for m in winners_matches:
        if m.next_match_id is None:
            # This is the WB Finals match
            m.next_match_id = grand_final_id  # Winner goes to Grand Final
            # Only set loser_next_match_id if LB Finals exists
            if num_lb_rounds > 0 and num_lb_rounds in lb_by_round and len(lb_by_round[num_lb_rounds]) > 0:
                m.loser_next_match_id = lb_finals_id  # Loser goes to LB Finals
                print(f"=== DEBUG: WB Finals {m.match_id} -> Winner: {grand_final_id}, Loser: {lb_finals_id} ===")
            else:
                print(f"=== DEBUG: WB Finals {m.match_id} -> Winner: {grand_final_id}, No LB Finals (tournament ends) ===")
            break
    
    # Process bye winners in the losers bracket
    _process_bye_winners(losers_matches)
    
    return winners_matches, losers_matches, grand_final_match, num_rounds


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
