# Know-Zone - Academic Integrity "Would You Rather" Game

Interactive web-based game where students answer "Would You Rather" questions to test their knowledge of academic values.

## Features

- Create or join game sessions with unique 3-digit codes
- AI-generated personalized questions (with fallback questions)
- Real-time progress tracking for both players
- Automatic score calculation and leaderboard
- Session persistence (survives server restarts)
- Responsive design for desktop and mobile

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```
OPENROUTER_API_KEY=your_key_here
```

Or use OpenAI:

```
OPENAI_API_KEY=your_key_here
```

If no API key is provided, the app will use fallback questions.

## Run

```bash
python app.py
```

Access at: http://localhost:5000

## Project Structure

```
Know-Zone/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Frontend
├── open_ai/
│   └── ai.py             # AI question generation
├── instance/
│   └── quiz_game.db      # SQLite database
└── requirements.txt       # Dependencies
```

## License

Open source for educational purposes.
