# Leaderboard Integration Guide

## 1. Displaying the Leaderboard

Update your leaderboard display to show more detailed information about the competitors:

\`\`\`javascript
function updateLeaderboardDisplay(elementId) {
  fetch('http://localhost:5000/api/leaderboard')
    .then(response => response.json())
    .then(data => {
      const leaderboardBody = document.getElementById(elementId);
      leaderboardBody.innerHTML = '';
      
      data.forEach((entry, index) => {
        const row = document.createElement('tr');
        let medalClass = '';
        if (index === 0) medalClass = 'gold';
        else if (index === 1) medalClass = 'silver';
        else if (index === 2) medalClass = 'bronze';
        
        const medal = medalClass ? `<span class="medal ${medalClass}">${index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}</span>` : '';
        
        // Format player names
        const playerNames = entry.players.map(player => player.username).join(' & ');
        
        row.innerHTML = `
          <td>${medal}${index + 1}</td>
          <td>${playerNames}</td>
          <td>${entry.matches}/10</td>
          <td>${entry.date}</td>
        `;
        leaderboardBody.appendChild(row);
      });
    })
    .catch(error => {
      console.error('Error:', error);
    });
}
\`\`\`

## 2. Player Profile and Stats

Add a player profile section to display individual player statistics:

```html
<div id="player-profile" class="hidden">
  <h2>Player Profile: <span id="profile-username"></span></h2>
  <div class="player-stats">
    <div class="stat-card">
      <h3>Games Played</h3>
      <p id="profile-games-played">0</p>
    </div>
    <div class="stat-card">
      <h3>Average Score</h3>
      <p id="profile-avg-score">0</p>
    </div>
    <div class="stat-card">
      <h3>Best Score</h3>
      <p id="profile-best-score">0</p>
    </div>
    <div class="stat-card">
      <h3>Rank</h3>
      <p id="profile-rank">-</p>
    </div>
  </div>
  
  <h3>Recent Games</h3>
  <table class="leaderboard-table">
    <thead>
      <tr>
        <th>Date</th>
        <th>Opponent</th>
        <th>Matches</th>
      </tr>
    </thead>
    <tbody id="recent-games-body">
      &lt;!-- Recent games will be populated here -->
    </tbody>
  </table>
  
  <button onclick="showScreen('menu-screen')">Back to Menu</button>
</div>
