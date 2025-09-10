"""
Leaderboard API endpoints for the Would You Rather Quiz Game
"""
from flask import Blueprint, jsonify, request
from database_models import db, LeaderboardEntry, LeaderboardPlayerEntry, PlayerStats, User
from sqlalchemy import desc, func

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get the top leaderboard entries"""
    limit = request.args.get('limit', 10, type=int)
    
    # Get top entries by matches
    entries = LeaderboardEntry.query.order_by(desc(LeaderboardEntry.matches)).limit(limit).all()
    
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
    
    return jsonify(result)

@leaderboard_bp.route('/api/leaderboard/player/<username>', methods=['GET'])
def get_player_leaderboard(username):
    """Get leaderboard entries for a specific player"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Player not found'}), 404
    
    # Get entries where this player participated
    player_entries = LeaderboardPlayerEntry.query.filter_by(user_id=user.id).all()
    leaderboard_ids = [entry.leaderboard_id for entry in player_entries]
    
    entries = LeaderboardEntry.query.filter(LeaderboardEntry.id.in_(leaderboard_ids)).order_by(desc(LeaderboardEntry.matches)).all()
    
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
    
    return jsonify(result)

@leaderboard_bp.route('/api/leaderboard/stats', methods=['GET'])
def get_leaderboard_stats():
    """Get overall leaderboard statistics"""
    # Get top players by average score
    top_players = PlayerStats.query.order_by(desc(PlayerStats.average_match_score)).limit(10).all()
    
    # Get highest match score
    highest_match = LeaderboardEntry.query.order_by(desc(LeaderboardEntry.matches)).first()
    
    # Get total games played
    total_games = LeaderboardEntry.query.count()
    
    # Get average match score across all games
    avg_match_score = db.session.query(func.avg(LeaderboardEntry.matches)).scalar() or 0
    
    result = {
        'top_players': [{
            'username': player.user.username,
            'games_played': player.games_played,
            'average_score': player.average_match_score,
            'best_score': player.best_match_score
        } for player in top_players],
        'highest_match': highest_match.matches if highest_match else 0,
        'total_games': total_games,
        'average_match_score': float(avg_match_score)
    }
    
    return jsonify(result)

@leaderboard_bp.route('/api/leaderboard/player_stats/<username>', methods=['GET'])
def get_player_stats(username):
    """Get detailed stats for a specific player"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Player not found'}), 404
    
    stats = PlayerStats.query.filter_by(user_id=user.id).first()
    if not stats:
        return jsonify({
            'username': username,
            'games_played': 0,
            'total_matches': 0,
            'best_match_score': 0,
            'average_match_score': 0.0
        })
    
    # Get player's rank
    rank_query = db.session.query(
        func.count(PlayerStats.id) + 1
    ).filter(
        PlayerStats.average_match_score > stats.average_match_score
    ).scalar()
    
    # Get recent games
    player_entries = LeaderboardPlayerEntry.query.filter_by(user_id=user.id).order_by(
        LeaderboardPlayerEntry.id.desc()
    ).limit(5).all()
    
    recent_games = []
    for entry in player_entries:
        leaderboard_entry = entry.leaderboard_entry
        opponent_entry = next(
            (pe for pe in leaderboard_entry.player_entries if pe.user_id != user.id), 
            None
        )
        
        if opponent_entry:
            recent_games.append({
                'date': leaderboard_entry.date.strftime('%m/%d/%Y'),
                'opponent': opponent_entry.user.username,
                'matches': leaderboard_entry.matches
            })
    
    result = {
        'username': username,
        'games_played': stats.games_played,
        'total_matches': stats.total_matches,
        'best_match_score': stats.best_match_score,
        'average_match_score': stats.average_match_score,
        'rank': rank_query or 1,
        'recent_games': recent_games
    }
    
    return jsonify(result)
