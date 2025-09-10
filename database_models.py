"""
Database models for the Would You Rather Quiz Game
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player_stats = db.relationship('PlayerStats', backref='user', uselist=False, cascade='all, delete-orphan')

class GameSession(db.Model):
    code = db.Column(db.String(3), primary_key=True)
    host_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='waiting')  # waiting, in_progress, completed
    current_question = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    host = db.relationship('User', backref='hosted_sessions')
    players = db.relationship('Player', backref='game_session', cascade='all, delete-orphan')
    leaderboard_entry = db.relationship('LeaderboardEntry', backref='game_session', uselist=False, cascade='all, delete-orphan')

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    session_code = db.Column(db.String(3), db.ForeignKey('game_session.code'), nullable=False)
    answers = db.Column(db.Text, default='[]')  # JSON string of answers
    score = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', backref='player_sessions')
    
    def get_answers(self):
        return json.loads(self.answers)
    
    def set_answers(self, answers_list):
        self.answers = json.dumps(answers_list)

class LeaderboardEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_code = db.Column(db.String(3), db.ForeignKey('game_session.code'), nullable=False)
    matches = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player_entries = db.relationship('LeaderboardPlayerEntry', backref='leaderboard_entry', cascade='all, delete-orphan')

class LeaderboardPlayerEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    leaderboard_id = db.Column(db.Integer, db.ForeignKey('leaderboard_entry.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.Text, default='[]')  # JSON string of answers
    
    # Relationships
    user = db.relationship('User', backref='leaderboard_entries')
    
    def get_answers(self):
        return json.loads(self.answers)
    
    def set_answers(self, answers_list):
        self.answers = json.dumps(answers_list)

class PlayerStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False, unique=True)
    games_played = db.Column(db.Integer, default=0)
    total_matches = db.Column(db.Integer, default=0)
    best_match_score = db.Column(db.Integer, default=0)
    average_match_score = db.Column(db.Float, default=0.0)
    
    def calculate_average(self):
        if self.games_played > 0:
            self.average_match_score = self.total_matches / self.games_played
        else:
            self.average_match_score = 0.0
