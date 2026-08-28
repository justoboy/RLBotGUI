"""
Data structures for tournament management
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Participant:
    """Represents a tournament participant (bot or human)"""
    name: str
    participant_id: str  # Unique identifier
    participant_type: str  # 'bot' or 'human'
    bot_config: Optional[Dict[str, Any]] = None  # Bot configuration if participant_type is 'bot'
    seed: int = 0  # Seeding position
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'participant_id': self.participant_id,
            'participant_type': self.participant_type,
            'bot_config': self.bot_config,
            'seed': self.seed
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Participant':
        return Participant(
            name=data['name'],
            participant_id=data['participant_id'],
            participant_type=data['participant_type'],
            bot_config=data.get('bot_config'),
            seed=data.get('seed', 0)
        )


@dataclass
class Team:
    """Represents a team in the tournament (1v1, 2v2, 3v3, 4v4, or 5v5)"""
    team_id: str
    name: str  # Optional custom name (e.g., 'Team A')
    participants: List[Participant] = field(default_factory=list)
    wins: int = 0
    losses: int = 0
    points: int = 0  # For round robin
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'team_id': self.team_id,
            'name': self.name,
            'participants': [p.to_dict() for p in self.participants],
            'wins': self.wins,
            'losses': self.losses,
            'points': self.points
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Team':
        team = Team(
            team_id=data['team_id'],
            name=data.get('name', ''),
            wins=data.get('wins', 0),
            losses=data.get('losses', 0),
            points=data.get('points', 0)
        )
        for p_data in data.get('participants', []):
            team.participants.append(Participant.from_dict(p_data))
        return team


@dataclass
class Match:
    """Represents a single match in the tournament"""
    match_id: str
    round_num: int  # 1 = first round, 2 = second round, etc.
    participant1: Optional[Participant] = None
    participant2: Optional[Participant] = None
    winner: Optional[Participant] = None
    score: Optional[tuple] = None  # (score1, score2)
    completed: bool = False
    next_match_id: Optional[str] = None  # Match this winner advances to
    loser_next_match_id: Optional[str] = None  # For double elimination: match loser advances to
    # Team-based fields (Phase 2): when team_size > 1, matches are between teams
    team1: Optional[Team] = None
    team2: Optional[Team] = None
    winner_team: Optional[Team] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'match_id': self.match_id,
            'round_num': self.round_num,
            'participant1': self.participant1.to_dict() if self.participant1 else None,
            'participant2': self.participant2.to_dict() if self.participant2 else None,
            'winner': self.winner.to_dict() if self.winner else None,
            'score': self.score,
            'completed': self.completed,
            'next_match_id': self.next_match_id,
            'loser_next_match_id': self.loser_next_match_id,
            'team1': self.team1.to_dict() if self.team1 else None,
            'team2': self.team2.to_dict() if self.team2 else None,
            'winner_team': self.winner_team.to_dict() if self.winner_team else None
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Match':
        match = Match(
            match_id=data['match_id'],
            round_num=data['round_num'],
            completed=data.get('completed', False),
            next_match_id=data.get('next_match_id'),
            loser_next_match_id=data.get('loser_next_match_id')
        )
        if data.get('participant1'):
            match.participant1 = Participant.from_dict(data['participant1'])
        if data.get('participant2'):
            match.participant2 = Participant.from_dict(data['participant2'])
        if data.get('winner'):
            match.winner = Participant.from_dict(data['winner'])
        if data.get('score'):
            match.score = tuple(data['score'])
        if data.get('team1'):
            match.team1 = Team.from_dict(data['team1'])
        if data.get('team2'):
            match.team2 = Team.from_dict(data['team2'])
        if data.get('winner_team'):
            match.winner_team = Team.from_dict(data['winner_team'])
        return match


@dataclass
class TournamentState:
    """Represents the complete state of a tournament"""
    name: str
    tournament_id: str
    format: str  # 'single_elimination', 'double_elimination', 'round_robin'
    participants: List[Participant] = field(default_factory=list)
    matches: List[Match] = field(default_factory=list)
    current_round: int = 1
    completed: bool = False
    winner: Optional[Participant] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    losers_bracket_matches: List[Match] = field(default_factory=list)  # For double elimination
    match_settings: Dict[str, Any] = field(default_factory=dict)  # Custom match settings/mutators
    # Phase 2: team size support (1v1, 2v2, 3v3, 4v4, 5v5)
    team_size: int = 1  # 1, 2, 3, 4, or 5 participants per team
    teams: List[Team] = field(default_factory=list)  # Formed teams
    winner_team: Optional[Team] = None  # Winning team (when team_size > 1)
    # Party-mode: allow the same bot to be duplicated within a team
    allow_duplicates: bool = False  # When True, each team member is a copy of one participant
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'tournament_id': self.tournament_id,
            'format': self.format,
            'participants': [p.to_dict() for p in self.participants],
            'matches': [m.to_dict() for m in self.matches],
            'current_round': self.current_round,
            'completed': self.completed,
            'winner': self.winner.to_dict() if self.winner else None,
            'created_at': self.created_at,
            'losers_bracket_matches': [m.to_dict() for m in self.losers_bracket_matches],
            'match_settings': self.match_settings,
            'team_size': self.team_size,
            'teams': [t.to_dict() for t in self.teams],
            'winner_team': self.winner_team.to_dict() if self.winner_team else None,
            'allow_duplicates': self.allow_duplicates
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TournamentState':
        state = TournamentState(
            name=data['name'],
            tournament_id=data['tournament_id'],
            format=data['format'],
            current_round=data.get('current_round', 1),
            completed=data.get('completed', False),
            created_at=data.get('created_at', datetime.now().isoformat()),
            match_settings=data.get('match_settings', {}),
            team_size=data.get('team_size', 1),
            allow_duplicates=data.get('allow_duplicates', False)
        )
        for p_data in data.get('participants', []):
            state.participants.append(Participant.from_dict(p_data))
        for m_data in data.get('matches', []):
            state.matches.append(Match.from_dict(m_data))
        for m_data in data.get('losers_bracket_matches', []):
            state.losers_bracket_matches.append(Match.from_dict(m_data))
        for t_data in data.get('teams', []):
            state.teams.append(Team.from_dict(t_data))
        if data.get('winner'):
            state.winner = Participant.from_dict(data['winner'])
        if data.get('winner_team'):
            state.winner_team = Team.from_dict(data['winner_team'])
        return state
