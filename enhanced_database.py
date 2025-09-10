"""
Enhanced database integration for the Would You Rather Quiz Game
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid

db = SQLAlchemy()

def setup_database(app):
    """Initialize and setup the database"""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_game.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

def add_game_to_leaderboard(game_session):
    """Add a completed game to the leaderboard"""
    with db.session.begin():
        # Get player IDs
        player_ids = list(game_session['players'].keys())
        player1_id, player2_id = player_ids[0], player_ids[1]
        player1 = game_session['players'][player1_id]
        player2 = game_session['players'][player2_id]
        
        # Calculate matching answers
        matching_answers = 0
        for i in range(len(game_session['questions'])):
            if player1['answers'][i] == player2['answers'][i]:
                matching_answers += 1
        
        # Create leaderboard entry
        entry = LeaderboardEntry(
            session_code=game_session['session_code'],
            matches=matching_answers,
            date=datetime.now()
        )
        db.session.add(entry)
        db.session.flush()  # Get the ID of the new entry
        
        # Add player entries
        for player_id, player_data in game_session['players'].items():
            # Get or create user
            user = User.query.filter_by(id=player_id).first()
            if not user:
                user = User(
                    id=player_id,
                    username=player_data['username']
                )
                db.session.add(user)
                db.session.flush()
            
            # Create player entry
            player_entry = LeaderboardPlayerEntry(
                leaderboard_id=entry.id,
                user_id=user.id
            )
            player_entry.set_answers(player_data['answers'])
            db.session.add(player_entry)
            
            # Update player stats
            stats = PlayerStats.query.filter_by(user_id=user.id).first()
            if not stats:
                stats = PlayerStats(user_id=user.id)
                db.session.add(stats)
            
            stats.games_played += 1
            stats.total_matches += matching_answers
            stats.best_match_score = max(stats.best_match_score, matching_answers)
            stats.calculate_average()
        
        # Commit the transaction
        db.session.commit()
        
        return entry.id

def get_leaderboard(limit=10):
    """Get the top leaderboard entries"""
    entries = LeaderboardEntry.query.order_by(
        LeaderboardEntry.matches.desc()
    ).limit(limit).all()
    
    result = []
    for entry in entries:
        player_entries = []
        for player_entry in entry.player_entries:
            player_entries.append({
                'username': player_entry.user.username,
                'answers': player_entry.get_answers()
            })
        
        result.append({
            'id': entry.id,
            'players': player_entries,
            'matches': entry.matches,
            'date': entry.date.strftime('%m/%d/%Y')
        })
    
    return result
