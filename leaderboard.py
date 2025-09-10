"""
Leaderboard module for the Would You Rather Quiz Game
This module handles leaderboard operations and statistics
"""

class Leaderboard:
    def __init__(self):
        self.entries = []
        self.player_stats = {}
    
    def add_entry(self, entry):
        """Add a new entry to the leaderboard"""
        self.entries.append(entry)
        self.entries.sort(key=lambda x: x['matches'], reverse=True)
        
        # Keep only top 10
        if len(self.entries) > 10:
            self.entries = self.entries[:10]
        
        # Update player stats
        for player in entry['players']:
            self.update_player_stats(player['username'], entry['matches'])
    
    def update_player_stats(self, username, matches):
        """Update statistics for a player"""
        if username not in self.player_stats:
            self.player_stats[username] = {
                'username': username,
                'games_played': 0,
                'total_matches': 0,
                'best_match_score': 0,
                'average_match_score': 0,
                'match_history': []
            }
        
        stats = self.player_stats[username]
        stats['games_played'] += 1
        stats['total_matches'] += matches
        stats['best_match_score'] = max(stats['best_match_score'], matches)
        stats['average_match_score'] = stats['total_matches'] / stats['games_played']
        stats['match_history'].append(matches)
    
    def get_top_players(self, limit=10):
        """Get top players based on average match score"""
        players = list(self.player_stats.values())
        players.sort(key=lambda x: x['average_match_score'], reverse=True)
        return players[:limit]
    
    def get_player_stats(self, username):
        """Get stats for a specific player"""
        return self.player_stats.get(username)
    
    def get_all_entries(self):
        """Get all leaderboard entries"""
        return self.entries
    
    def get_player_rank(self, username):
        """Get the rank of a player based on average score"""
        if username not in self.player_stats:
            return None
        
        players = self.get_top_players(limit=None)
        for i, player in enumerate(players):
            if player['username'] == username:
                return i + 1
        
        return None
