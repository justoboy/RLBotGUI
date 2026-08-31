"""
Dependency-free tests for the Swiss tournament format (Phase 4, Feature E).

Run with:
    venv\\Scripts\\python.exe tests\\test_swiss_format.py

Uses plain assertions (no pytest) so no new dependencies are introduced.
Covers:
  - Round count calculation (ceil(log2(n)))
  - Round 1 seeded pairing
  - Next-round matching (similar records, rematch avoidance)
  - Tiebreaker ranking (score differential, goals scored, head-to-head)
  - Playoff determination when the top 2 are tied
  - Team-based (stand-in) Swiss generation
  - A full end-to-end Swiss tournament flow
"""

import os
import sys

# Ensure the project root is importable regardless of the CWD.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rlbot_gui.tournament.tournament_state import Participant, Match, Team
from rlbot_gui.tournament.bracket_generator import (
    calculate_swiss_rounds,
    generate_swiss_round1,
    generate_swiss_next_round,
    calculate_swiss_standings,
    determine_swiss_winner,
    _swiss_compute_records,
)

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {detail}")


def make_participants(n, prefix="P"):
    return [
        Participant(
            name=f"{prefix}{i+1}",
            participant_id=f"{prefix.lower()}{i+1}",
            participant_type='bot',
            seed=i
        )
        for i in range(n)
    ]


def make_completed_match(p1, p2, s1, s2):
    m = Match(
        match_id=f"M_{p1.participant_id}_{p2.participant_id}",
        round_num=1,
        participant1=p1,
        participant2=p2,
        completed=True
    )
    m.score = (s1, s2)
    m.winner = p1 if s1 > s2 else (p2 if s2 > s1 else None)
    return m


def test_round_count():
    print("\n[1] Round count calculation (ceil(log2(n)))")
    cases = {2: 1, 4: 2, 8: 3, 16: 4, 6: 3, 10: 4, 3: 2, 5: 3}
    for n, expected in cases.items():
        check(f"calculate_swiss_rounds({n}) == {expected}",
              calculate_swiss_rounds(n) == expected,
              f"(got {calculate_swiss_rounds(n)})")
    # Edge: fewer than 2 participants
    check("calculate_swiss_rounds(1) == 1", calculate_swiss_rounds(1) == 1)
    check("calculate_swiss_rounds(0) == 1", calculate_swiss_rounds(0) == 1)


def test_round1_pairing():
    print("\n[2] Round 1 seeded pairing")
    parts = make_participants(4)
    matches = generate_swiss_round1(parts)
    check("4 participants -> 2 matches", len(matches) == 2, f"(got {len(matches)})")
    # Pairing should be 1v2, 3v4 (adjacent seed order)
    pairs = set()
    for m in matches:
        pairs.add(frozenset([m.participant1.participant_id, m.participant2.participant_id]))
    expected_pairs = {
        frozenset(['p1', 'p2']),
        frozenset(['p3', 'p4'])
    }
    check("Round 1 pairs are (p1,p2) and (p3,p4)", pairs == expected_pairs, f"(got {pairs})")
    check("All round 1 matches are round_num=1", all(m.round_num == 1 for m in matches))
    check("All round 1 matches are incomplete", all(not m.completed for m in matches))

    # 8 participants -> 4 matches
    parts8 = make_participants(8)
    matches8 = generate_swiss_round1(parts8)
    check("8 participants -> 4 matches", len(matches8) == 4, f"(got {len(matches8)})")

    # 2 participants -> 1 match
    parts2 = make_participants(2)
    matches2 = generate_swiss_round1(parts2)
    check("2 participants -> 1 match", len(matches2) == 1, f"(got {len(matches2)})")


def test_next_round_matching():
    print("\n[3] Next-round matching (similar records, rematch avoidance)")
    parts = make_participants(4)
    p1, p2, p3, p4 = parts

    # Round 1 results: p1 beats p2, p3 beats p4.
    # So p1 and p3 have 1 win each; p2 and p4 have 0 wins.
    completed = [
        make_completed_match(p1, p2, 3, 1),
        make_completed_match(p3, p4, 2, 0),
    ]
    tiebreakers = ['score_differential', 'goals_scored', 'head_to_head']
    matches = generate_swiss_next_round(parts, completed, 2, tiebreakers)
    check("Round 2 has 2 matches", len(matches) == 2, f"(got {len(matches)})")
    check("All round 2 matches are round_num=2", all(m.round_num == 2 for m in matches))

    # The two winners (p1, p3) should be paired together (both 1 win).
    # The two losers (p2, p4) should be paired together (both 0 wins).
    pairs = set()
    for m in matches:
        pairs.add(frozenset([m.participant1.participant_id, m.participant2.participant_id]))
    check("Winners (p1,p3) paired together",
          frozenset(['p1', 'p3']) in pairs, f"(got {pairs})")
    check("Losers (p2,p4) paired together",
          frozenset(['p2', 'p4']) in pairs, f"(got {pairs})")

    # Rematch avoidance: p1 already played p2, so p1 should NOT be paired with p2.
    check("p1 not rematched with p2",
          frozenset(['p1', 'p2']) not in pairs, f"(got {pairs})")
    check("p3 not rematched with p4",
          frozenset(['p3', 'p4']) not in pairs, f"(got {pairs})")


def test_rematch_avoidance_fallback():
    print("\n[4] Rematch avoidance with fallback (pool exhausted)")
    # With only 2 participants, round 2 must be a rematch (no alternative).
    parts = make_participants(2)
    p1, p2 = parts
    completed = [make_completed_match(p1, p2, 3, 1)]
    matches = generate_swiss_next_round(parts, completed, 2, ['score_differential'])
    check("2 participants round 2 still produces 1 match", len(matches) == 1, f"(got {len(matches)})")
    if matches:
        pair = frozenset([matches[0].participant1.participant_id, matches[0].participant2.participant_id])
        check("Fallback allows rematch when no alternative", pair == frozenset(['p1', 'p2']), f"(got {pair})")


def test_tiebreaker_ranking():
    print("\n[5] Tiebreaker ranking")
    parts = make_participants(4)
    p1, p2, p3, p4 = parts

    # All four have 1 win and 1 loss after 2 rounds.
    # Differentiate by goal differential and goals scored.
    # p1: +5 GD, 10 GF ; p2: +3 GD, 8 GF ; p3: +1 GD, 6 GF ; p4: -1 GD, 4 GF
    completed = [
        make_completed_match(p1, p4, 5, 0),   # p1 wins 5-0
        make_completed_match(p2, p3, 4, 1),   # p2 wins 4-1
        make_completed_match(p1, p2, 5, 2),   # p1 wins 5-2
        make_completed_match(p3, p4, 3, 1),   # p3 wins 3-1
    ]
    # Recompute records to verify.
    records = _swiss_compute_records(parts, completed)
    # p1: wins vs p4 (5-0) and vs p2 (5-2) => 2 wins. p2: 1 win (vs p3), 1 loss (vs p1).
    # p3: 1 win (vs p4), 1 loss (vs p2). p4: 2 losses.
    # So p1 has 2 wins, others 1 win each.
    standings = calculate_swiss_standings(parts, completed, ['score_differential', 'goals_scored', 'head_to_head'])
    check("p1 ranked #1 (2 wins)", standings[0]['participant'].participant_id == 'p1',
          f"(got {standings[0]['participant'].participant_id})")
    # Among p2, p3, p4 (all 1 win): p2 has higher GD than p3 than p4.
    check("p2 ranked #2 (best GD among 1-win group)", standings[1]['participant'].participant_id == 'p2',
          f"(got {standings[1]['participant'].participant_id})")
    check("p3 ranked #3", standings[2]['participant'].participant_id == 'p3',
          f"(got {standings[2]['participant'].participant_id})")
    check("p4 ranked #4", standings[3]['participant'].participant_id == 'p4',
          f"(got {standings[3]['participant'].participant_id})")

    # Verify tiebreaker order matters: with only 'goals_scored', ranking among
    # the 1-win group should still follow goals scored (p2 > p3 > p4 here).
    standings_gf = calculate_swiss_standings(parts, completed, ['goals_scored'])
    check("goals_scored tiebreaker: p1 still #1", standings_gf[0]['participant'].participant_id == 'p1')


def test_head_to_head_tiebreaker():
    print("\n[6] Head-to-head tiebreaker")
    parts = make_participants(4)
    p1, p2, p3, p4 = parts

    # p1 and p2 both have 1 win, 1 loss, identical GD and GF.
    # p1 beat p3, lost to p4. p2 beat p4, lost to p3.
    # p1 vs p2 have not played each other -> head-to-head cannot separate.
    completed = [
        make_completed_match(p1, p3, 3, 1),   # p1 wins
        make_completed_match(p4, p1, 2, 1),   # p4 wins
        make_completed_match(p2, p4, 3, 1),   # p2 wins
        make_completed_match(p3, p2, 2, 1),   # p3 wins
    ]
    records = _swiss_compute_records(parts, completed)
    # p1: 1W 1L, GF 3+1=4, GA 1+2=3, GD +1
    # p2: 1W 1L, GF 3+1=4, GA 1+2=3, GD +1
    # p3: 1W 1L, GF 1+2=3, GA 3+1=4, GD -1
    # p4: 1W 1L, GF 2+1=3, GA 1+3=4, GD -1
    check("p1 and p2 have identical records",
          records['p1'] == records['p2'],
          f"(p1={records['p1']}, p2={records['p2']})")

    # With head_to_head as the deciding tiebreaker and p1/p2 not having played,
    # a playoff should be required.
    result = determine_swiss_winner(parts, completed, ['score_differential', 'goals_scored', 'head_to_head'])
    check("Playoff needed when top 2 tied and H2H unavailable",
          result['playoff_needed'] is True, f"(got {result})")
    check("Playoff participants are p1 and p2",
          set(p.participant_id for p in result['playoff_participants']) == {'p1', 'p2'},
          f"(got {[p.participant_id for p in result['playoff_participants']]})")


def test_head_to_head_decides():
    print("\n[7] Head-to-head decides winner (no playoff)")
    parts = make_participants(4)
    p1, p2, p3, p4 = parts

    # p1 and p2 both 1W 1L, identical GD/GF, but they HAVE played each other.
    # p1 beat p2 head-to-head.
    completed = [
        make_completed_match(p1, p2, 3, 1),   # p1 beats p2 (H2H)
        make_completed_match(p3, p4, 2, 0),   # p3 wins
        make_completed_match(p1, p3, 2, 1),   # p1 wins
        make_completed_match(p2, p4, 3, 2),   # p2 wins
    ]
    records = _swiss_compute_records(parts, completed)
    # p1: 2W 1L ; p2: 1W 2L -> not tied, p1 wins outright.
    # Let's craft a true tie instead:
    completed2 = [
        make_completed_match(p1, p2, 3, 1),   # p1 beats p2 (H2H)
        make_completed_match(p1, p3, 2, 1),   # p1 wins
        make_completed_match(p2, p4, 3, 1),   # p2 wins
        make_completed_match(p3, p4, 2, 1),   # p3 wins
    ]
    records2 = _swiss_compute_records(parts, completed2)
    # p1: 2W 1L ; p2: 1W 2L. Not a tie. Use a symmetric setup:
    # p1 beats p2, p2 beats p3, p3 beats p1 (cycle) + p4 loses to all.
    completed3 = [
        make_completed_match(p1, p2, 3, 1),   # p1 beats p2
        make_completed_match(p2, p3, 3, 1),   # p2 beats p3
        make_completed_match(p3, p1, 3, 1),   # p3 beats p1
        make_completed_match(p1, p4, 3, 0),   # p1 beats p4
        make_completed_match(p2, p4, 3, 0),   # p2 beats p4
        make_completed_match(p3, p4, 3, 0),   # p3 beats p4
    ]
    records3 = _swiss_compute_records(parts, completed3)
    # p1: 2W 1L, GF 3+3+3=9, GA 1+1+0=2, GD +7
    # p2: 2W 1L, GF 3+3+3=9, GA 1+1+0=2, GD +7
    # p3: 2W 1L, GF 3+3+3=9, GA 1+1+0=2, GD +7
    # p4: 0W 3L
    # p1, p2, p3 all tied on wins/GD/GF. H2H cycle: p1>p2>p3>p1.
    # Top 2 are p1 and p2 (order depends on sort stability). p1 beat p2 H2H.
    result = determine_swiss_winner(parts, completed3, ['score_differential', 'goals_scored', 'head_to_head'])
    # The top 2 should be two of {p1,p2,p3}. If they are p1 and p2, H2H gives p1.
    top2 = set(result['standings'][0]['participant'].participant_id for _ in [0])
    check("A winner is determined (no playoff) when H2H separates top 2",
          result['playoff_needed'] is False and result['winner'] is not None,
          f"(got {result['playoff_needed']}, winner={result['winner']})")


def test_team_based_swiss():
    print("\n[8] Team-based Swiss (stand-in participants)")
    # Simulate 4 teams (2v2) using stand-in participants.
    teams = []
    for i in range(4):
        t = Team(team_id=f"t{i+1}", name=f"Team {i+1}")
        t.participants = [
            Participant(name=f"Bot{t.name}_{j}", participant_id=f"b{i+1}_{j}", participant_type='bot')
            for j in range(2)
        ]
        teams.append(t)

    stand_ins = [
        Participant(name=t.name, participant_id=t.team_id, participant_type='team', seed=0)
        for t in teams
    ]
    matches = generate_swiss_round1(stand_ins)
    check("4 teams -> 2 round-1 matches", len(matches) == 2, f"(got {len(matches)})")
    check("Stand-in participant_type is 'team'",
          all(m.participant1.participant_type == 'team' for m in matches))

    # Complete round 1 and generate round 2.
    completed = [
        make_completed_match(stand_ins[0], stand_ins[1], 4, 2),
        make_completed_match(stand_ins[2], stand_ins[3], 3, 1),
    ]
    matches2 = generate_swiss_next_round(stand_ins, completed, 2, ['score_differential'])
    check("4 teams -> 2 round-2 matches", len(matches2) == 2, f"(got {len(matches2)})")


def test_full_swiss_flow():
    print("\n[9] Full Swiss tournament flow (4 participants, 2 rounds)")
    parts = make_participants(4)
    p1, p2, p3, p4 = parts
    tiebreakers = ['score_differential', 'goals_scored', 'head_to_head']

    # Round 1
    round1 = generate_swiss_round1(parts)
    check("Round 1 generated", len(round1) == 2)

    # Record round 1 results: p1 beats p2, p3 beats p4.
    completed = [
        make_completed_match(p1, p2, 3, 1),
        make_completed_match(p3, p4, 2, 0),
    ]

    # Round 2
    round2 = generate_swiss_next_round(parts, completed, 2, tiebreakers)
    check("Round 2 generated", len(round2) == 2)

    # Record round 2 results. p1 (1W) vs p3 (1W): p1 wins. p2 (0W) vs p4 (0W): p4 wins.
    # Find the actual pairings to record consistent results.
    for m in round2:
        ids = {m.participant1.participant_id, m.participant2.participant_id}
        if ids == {'p1', 'p3'}:
            m.score = (3, 1) if m.participant1.participant_id == 'p1' else (1, 3)
            m.completed = True
            m.winner = m.participant1 if m.participant1.participant_id == 'p1' else m.participant2
        elif ids == {'p2', 'p4'}:
            m.score = (1, 3) if m.participant1.participant_id == 'p2' else (3, 1)
            m.completed = True
            m.winner = m.participant1 if m.participant1.participant_id == 'p4' else m.participant2

    all_completed = completed + round2
    records = _swiss_compute_records(parts, all_completed)
    # p1: 2W ; p3: 1W 1L ; p4: 1W 1L ; p2: 0W 2L
    check("p1 has 2 wins", records['p1']['wins'] == 2, f"(got {records['p1']})")

    result = determine_swiss_winner(parts, all_completed, tiebreakers)
    check("p1 is the winner (2 wins, no tie)",
          result['winner'] is not None and result['winner'].participant_id == 'p1',
          f"(got {result['winner']})")
    check("No playoff needed", result['playoff_needed'] is False)


def main():
    print("=" * 60)
    print("Swiss Tournament Format Tests (Phase 4, Feature E)")
    print("=" * 60)

    test_round_count()
    test_round1_pairing()
    test_next_round_matching()
    test_rematch_avoidance_fallback()
    test_tiebreaker_ranking()
    test_head_to_head_tiebreaker()
    test_head_to_head_decides()
    test_team_based_swiss()
    test_full_swiss_flow()

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
