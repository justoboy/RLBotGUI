"""
Double Elimination Bracket Test Script

This script tests the double elimination bracket generation and progression
by simulating matches with random winners and verifying correct advancement.

Run with: python -m pytest tests/test_double_elimination.py -v
Or: python tests/test_double_elimination.py
"""

import sys
import os
import random
import math
from typing import List, Dict, Optional, Tuple, Any

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the actual Match and Participant classes from the module
from rlbot_gui.tournament.tournament_state import Match, Participant

# Import the bracket generator
from rlbot_gui.tournament.bracket_generator import generate_double_elimination_bracket, seed_bracket, _process_bye_winners


# Set seed for reproducibility (change or remove for random results)
random.seed(42)


def generate_random_participants(count: int) -> List[Participant]:
    """Generate random participants for testing."""
    names = [
        "BotAlpha", "BotBeta", "BotGamma", "BotDelta", "BotEpsilon",
        "BotZeta", "BotEta", "BotTheta", "BotIota", "BotKappa",
        "BotLambda", "BotMu", "BotNu", "BotXi", "BotOmicron",
        "BotPi", "BotRho", "BotSigma", "BotTau", "BotUpsilon",
        "BotPhi", "BotChi", "BotPsi", "BotOmega", "BotA", "BotB",
        "BotC", "BotD", "BotE", "BotF", "BotG", "BotH", "BotI",
        "BotJ", "BotK", "BotL", "BotM", "BotN", "BotO", "BotP",
        "BotQ", "BotR", "BotS", "BotT", "BotU", "BotV", "BotW",
        "BotX", "BotY", "BotZ", "BotOne", "BotTwo", "BotThree",
        "BotFour", "BotFive", "BotSix", "BotSeven", "BotEight",
        "BotNine", "BotTen", "BotEleven", "BotTwelve", "BotThirteen",
        "BotFourteen", "BotFifteen", "BotSixteen", "BotSeventeen",
        "BotEighteen", "BotNineteen", "BotTwenty", "BotTwentyOne",
        "BotTwentyTwo", "BotTwentyThree", "BotTwentyFour", "BotTwentyFive",
        "BotTwentySix", "BotTwentySeven", "BotTwentyEight", "BotTwentyNine",
        "BotThirty", "BotThirtyOne", "BotThirtyTwo", "BotThirtyThree",
        "BotThirtyFour", "BotThirtyFive", "BotThirtySix", "BotThirtySeven",
        "BotThirtyEight", "BotThirtyNine", "BotForty", "BotFortyOne",
        "BotFortyTwo", "BotFortyThree", "BotFortyFour", "BotFortyFive",
        "BotFortySix", "BotFortySeven", "BotFortyEight", "BotFortyNine",
        "BotFifty", "BotFiftyOne", "BotFiftyTwo", "BotFiftyThree",
        "BotFiftyFour", "BotFiftyFive", "BotFiftySix", "BotFiftySeven",
        "BotFiftyEight", "BotFiftyNine", "BotSixty", "BotSixtyOne",
        "BotSixtyTwo", "BotSixtyThree", "BotSixtyFour", "BotSixtyFive",
        "BotSixtySix", "BotSixtySeven", "BotSixtyEight", "BotSixtyNine",
        "BotSeventy", "BotSeventyOne", "BotSeventyTwo", "BotSeventyThree",
        "BotSeventyFour", "BotSeventyFive", "BotSeventySix", "BotSeventySeven",
        "BotSeventyEight", "BotSeventyNine", "BotEighty", "BotEightyOne",
        "BotEightyTwo", "BotEightyThree", "BotEightyFour", "BotEightyFive",
        "BotEightySix", "BotEightySeven", "BotEightyEight", "BotEightyNine",
        "BotNinety", "BotNinetyOne", "BotNinetyTwo", "BotNinetyThree",
        "BotNinetyFour", "BotNinetyFive", "BotNinetySix", "BotNinetySeven",
        "BotNinetyEight", "BotNinetyNine", "BotHundred"
    ]
    
    participants = []
    for i in range(count):
        name = names[i] if i < len(names) else f"Bot{i}"
        participants.append(Participant(
            name=name,
            participant_id=str(i),  # participant_id must be a string
            participant_type='bot',
            seed=i + 1
        ))
    
    return participants


def get_match_participants(match: Match) -> Tuple[Optional[Participant], Optional[Participant]]:
    """Get the participants of a match."""
    return match.participant1, match.participant2


def simulate_match(match: Match) -> Optional[Participant]:
    """Simulate a match and return the winner."""
    p1, p2 = get_match_participants(match)
    
    if p1 is None and p2 is None:
        return None
    elif p1 is None:
        return p2
    elif p2 is None:
        return p1
    else:
        # Random winner
        winner = random.choice([p1, p2])
        return winner


def get_all_matches(tournament) -> List[Match]:
    """Get all matches from the tournament."""
    all_matches = list(tournament.matches)
    all_matches.extend(tournament.losers_bracket_matches)
    return all_matches


def get_matches_by_round(matches: List[Match], is_losers: bool = False) -> Dict[int, List[Match]]:
    """Group matches by round number."""
    result = {}
    for match in matches:
        round_num = match.round_num
        if round_num not in result:
            result[round_num] = []
        result[round_num].append(match)
    return result


def verify_no_orphans(tournament) -> bool:
    """Verify that all matches have valid participants or are TBD."""
    all_matches = get_all_matches(tournament)
    for match in all_matches:
        if match.completed:
            if match.winner is None:
                print(f"ERROR: Match {match.match_id} is completed but has no winner!")
                return False
    return True


def verify_tournament_completion(tournament) -> Tuple[bool, Optional[Participant]]:
    """Verify that the tournament completed and return the champion."""
    all_matches = get_all_matches(tournament)
    
    # Find the Grand Final match (highest round number)
    max_round = max(m.round_num for m in all_matches)
    grand_finals = [m for m in all_matches if m.round_num == max_round]
    
    if not grand_finals:
        print("ERROR: No Grand Final match found!")
        return False, None
    
    grand_final = grand_finals[0]
    
    if not grand_final.completed:
        print(f"ERROR: Grand Final {grand_final.match_id} is not completed!")
        return False, None
    
    return True, grand_final.winner


def run_tournament_simulation(num_participants: int, verbose: bool = False) -> Tuple[bool, Optional[Participant], str]:
    """
    Run a complete double elimination tournament simulation.
    
    The simulation follows the correct order:
    1. Process WB R1 → losers populate LB R1
    2. Process LB R1 → winners advance to LB R2
    3. Process WB R2 → losers populate LB R2
    4. Process LB R2 → winners advance to LB R3, losers from WB R2 now available
    5. Continue alternating between WB and LB as matches become ready
    
    Returns:
        Tuple of (success, champion, message)
    """
    print(f"\n{'='*60}")
    print(f"Testing Double Elimination with {num_participants} participants")
    print(f"{'='*60}")
    
    # Generate participants
    participants = generate_random_participants(num_participants)
    print(f"Generated {len(participants)} participants")
    
    # Generate bracket
    winners_matches, losers_matches, grand_final, num_rounds = generate_double_elimination_bracket(participants)
    
    if not winners_matches:
        return False, None, "Failed to generate winners bracket"
    
    print(f"Generated Winners Bracket: {len(winners_matches)} matches, {num_rounds} rounds")
    print(f"Generated Losers Bracket: {len(losers_matches)} matches")
    if grand_final:
        print(f"Generated Grand Final: {grand_final.match_id}")
    
    # Create a mock tournament state
    class MockTournament:
        def __init__(self):
            self.format = 'double_elimination'
            self.matches = winners_matches
            self.losers_bracket_matches = losers_matches
            if grand_final:
                self.matches.append(grand_final)
            self.teams = None
    
    tournament = MockTournament()
    
    # Get all matches
    all_matches = get_all_matches(tournament)
    completed_matches = set()
    
    # Initialize completed_matches with matches that were auto-completed during bracket generation
    # (e.g., bye vs bye matches that were auto-resolved)
    for match in all_matches:
        if match.completed and match.winner:
            completed_matches.add(match.match_id)
    
    def get_match_by_id(match_id: str) -> Optional[Match]:
        """Find a match by its ID."""
        for m in all_matches:
            if m.match_id == match_id:
                return m
        return None
    
    def get_ready_matches() -> List[Match]:
        """Get all matches that are ready to play (have at least one participant).
        
        Matches with both participants are regular matches.
        Matches with only one participant are bye matches - the existing participant advances.
        """
        ready = []
        for match in all_matches:
            if match.match_id in completed_matches:
                continue
            # Include matches with at least one participant
            if match.participant1 is not None or match.participant2 is not None:
                ready.append(match)
        return ready
    
    def should_process_as_bye(match):
        """
        Determine if a match with one participant should be processed as a bye.
        
        Rules:
        - WB matches: Always process as bye (no one drops into WB matches)
        - LB intermediate rounds: Process as bye
        - LB Finals (where WB Finals loser drops): Wait for both participants
        - Grand Final (WB winner vs LB Finals winner): Wait for both participants
        """
        # WB matches - always process as bye
        if match.match_id.startswith('W'):
            return True
        
        # Find WB Finals match
        wb_finals = None
        for m in all_matches:
            if m.match_id.startswith('W') and m.round_num == num_rounds:
                wb_finals = m
                break
        
        if wb_finals is None:
            # No WB Finals found, process as bye
            return True
        
        # Grand Final - wait for both participants
        if wb_finals.next_match_id == match.match_id:
            return False
        
        # LB Finals - wait for both participants
        if wb_finals.loser_next_match_id == match.match_id:
            return False
        
        # All other LB matches - process as bye
        return True
    
    def process_match(match: Match) -> bool:
        """
        Process a match: determine winner, advance to next match.
        Returns True if successful, False if match couldn't be processed.
        """
        p1, p2 = match.participant1, match.participant2
        
        if p1 is None and p2 is None:
            return False
        elif p1 is None:
            if not should_process_as_bye(match):
                # Not a bye - wait for second participant
                return False
            winner = p2
        elif p2 is None:
            if not should_process_as_bye(match):
                # Not a bye - wait for second participant
                return False
            winner = p1
        else:
            # Random winner
            winner = random.choice([p1, p2])
        
        if winner is None:
            return False
        
        # Mark match as completed
        match.completed = True
        match.winner = winner
        completed_matches.add(match.match_id)
        
        if verbose:
            p1_name = match.participant1.name if match.participant1 else "TBD"
            p2_name = match.participant2.name if match.participant2 else "TBD"
            print(f"  {match.match_id}: {p1_name} vs {p2_name} -> {winner.name}")
        
        # Advance winner to next match
        if match.next_match_id:
            next_match = get_match_by_id(match.next_match_id)
            if next_match:
                if next_match.participant1 is None:
                    next_match.participant1 = winner
                elif next_match.participant2 is None:
                    next_match.participant2 = winner
                else:
                    if verbose:
                        print(f"    WARNING: Next match {next_match.match_id} already has both participants!")
        
        # For WB matches, populate LB with loser
        if match.match_id.startswith('W') and match.loser_next_match_id:
            loser = None
            if match.participant1 and match.participant1 != winner:
                loser = match.participant1
            elif match.participant2 and match.participant2 != winner:
                loser = match.participant2
            
            if loser:
                lb_match = get_match_by_id(match.loser_next_match_id)
                if lb_match:
                    if lb_match.participant1 is None:
                        lb_match.participant1 = loser
                    elif lb_match.participant2 is None:
                        lb_match.participant2 = loser
                    else:
                        if verbose:
                            print(f"    WARNING: LB match {lb_match.match_id} already has both participants!")
        
        return True
    
    # Simulate in rounds to ensure correct order
    # We process matches round by round, alternating between WB and LB
    max_iterations = 10000
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Get all ready matches
        ready_matches = get_ready_matches()
        
        if not ready_matches:
            # No more matches ready - check if tournament is complete
            break
        
        # Process all ready matches
        for match in ready_matches:
            process_match(match)
    
    if iteration >= max_iterations:
        return False, None, f"Simulation exceeded max iterations ({max_iterations})"
    
    # Verify completion
    success, champion = verify_tournament_completion(tournament)
    
    if success:
        return True, champion, f"Tournament completed successfully. Champion: {champion.name}"
    else:
        # Find incomplete matches
        incomplete = [m for m in all_matches if not m.completed]
        if incomplete:
            return False, None, f"Tournament incomplete. {len(incomplete)} matches remaining."
        return False, None, "Tournament verification failed"


def test_small_brackets():
    """Test small bracket sizes."""
    print("\n" + "="*60)
    print("Testing Small Brackets (4, 5, 6, 7, 8 participants)")
    print("="*60)
    
    for count in [4, 5, 6, 7, 8]:
        success, champion, message = run_tournament_simulation(count, verbose=True)
        status = "PASS" if success else "FAIL"
        print(f"\n[{status}] {count} participants: {message}")


def test_medium_brackets():
    """Test medium bracket sizes."""
    print("\n" + "="*60)
    print("Testing Medium Brackets (16, 32 participants)")
    print("="*60)
    
    for count in [16, 32]:
        success, champion, message = run_tournament_simulation(count, verbose=False)
        status = "PASS" if success else "FAIL"
        print(f"\n[{status}] {count} participants: {message}")


def test_large_brackets():
    """Test large bracket sizes."""
    print("\n" + "="*60)
    print("Testing Large Brackets (50, 100 participants)")
    print("="*60)
    
    for count in [50, 100]:
        success, champion, message = run_tournament_simulation(count, verbose=False)
        status = "PASS" if success else "FAIL"
        print(f"\n[{status}] {count} participants: {message}")


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "="*60)
    print("Testing Edge Cases")
    print("="*60)
    
    # Test with 2 participants
    success, champion, message = run_tournament_simulation(2, verbose=True)
    status = "PASS" if success else "FAIL"
    print(f"\n[{status}] 2 participants: {message}")
    
    # Test with 3 participants
    success, champion, message = run_tournament_simulation(3, verbose=True)
    status = "PASS" if success else "FAIL"
    print(f"\n[{status}] 3 participants: {message}")
    
    # Test with 1 participant (edge case - should handle gracefully)
    print(f"\n[INFO] 1 participant: Skipping (not a valid tournament)")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("DOUBLE ELIMINATION BRACKET TEST SUITE")
    print("="*60)
    
    test_small_brackets()
    test_medium_brackets()
    test_large_brackets()
    test_edge_cases()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
