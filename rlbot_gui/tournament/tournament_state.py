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
            'loser_next_match_id': self.loser_next_match_id
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
            'losers_bracket_matches': [m.to_dict() for m in self.losers_bracket_matches]
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TournamentState':
        state = TournamentState(
            name=data['name'],
            tournament_id=data['tournament_id'],
            format=data['format'],
            current_round=data.get('current_round', 1),
            completed=data.get('completed', False),
            created_at=data.get('created_at', datetime.now().isoformat())
        )
        for p_data in data.get('participants', []):
            state.participants.append(Participant.from_dict(p_data))
        for m_data in data.get('matches', []):
            state.matches.append(Match.from_dict(m_data))
        for m_data in data.get('losers_bracket_matches', []):
            state.losers_bracket_matches.append(Match.from_dict(m_data))
        if data.get('winner'):
            state.winner = Participant.from_dict(data['winner'])
        return state
