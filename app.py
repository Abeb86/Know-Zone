from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import random
import string
import os
import json
from datetime import datetime
from ai_module.ai import generate_questions
import uuid

# Initialize Flask app with correct folder paths
app = Flask(__name__, 
            static_folder='../static',
            template_folder='../templates')
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GameSession(db.Model):
    code = db.Column(db.String(3), primary_key=True)
    student1_name = db.Column(db.String(100), nullable=False)
    student2_name = db.Column(db.String(100), nullable=True)
    student1_answers = db.Column(db.Text, default='[]')  # JSON string
    student2_answers = db.Column(db.Text, default='[]')  # JSON string
    student1_score = db.Column(db.Integer, default=0)
    student2_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='waiting')  # waiting, in_progress, completed
    current_question = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_student1_answers(self):
        return json.loads(self.student1_answers)
    
    def set_student1_answers(self, answers_list):
        self.student1_answers = json.dumps(answers_list)
    
    def get_student2_answers(self):
        return json.loads(self.student2_answers)
    
    def set_student2_answers(self, answers_list):
        self.student2_answers = json.dumps(answers_list)

class LeaderboardEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student1_name = db.Column(db.String(100), nullable=False)
    student2_name = db.Column(db.String(100), nullable=False)
    matching_answers = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# In-memory storage for backward compatibility during transition
active_sessions = {}

# Questions fallback (used if AI unavailable during app boot only)
questions = [
    {
        "question": "Would you rather...",
        "option1": "Copy someone else's homework the morning it's due",
        "option2": "Pay someone to write your final paper"
    },
    {
        "question": "Would you rather...",
        "option1": "Take an exam you didn't study for honestly",
        "option2": "Cheat but risk getting caught and failing the course"
    },
    {
        "question": "Would you rather...",
        "option1": "Work with a friend on an assignment meant to be individual",
        "option2": "Turn in an assignment late and lose points"
    },
    {
        "question": "Would you rather...",
        "option1": "Use ChatGPT to write your entire essay",
        "option2": "Submit a poorly written essay you actually wrote"
    },
    {
        "question": "Would you rather...",
        "option1": "Let a classmate copy your work knowing they'll keep doing it",
        "option2": "Refuse to share and risk the friendship"
    },
    {
        "question": "Would you rather...",
        "option1": "Take credit for a group project you barely contributed to",
        "option2": "Tell the professor you didn't do your fair share"
    },
    {
        "question": "Would you rather...",
        "option1": "Use a fake excuse to get an extension",
        "option2": "Submit incomplete work on time"
    },
    {
        "question": "Would you rather...",
        "option1": "Have your professor discover you plagiarized",
        "option2": "Never get caught but always know you cheated"
    },
    {
        "question": "Would you rather...",
        "option1": "Share test questions with friends after taking an exam",
        "option2": "Keep them to yourself knowing others might fail"
    },
    {
        "question": "Would you rather...",
        "option1": "Get an A by cheating in one important course",
        "option2": "Get a B by being honest in all your courses"
    }
]

# Helper function to generate a unique session code
def generate_session_code():
    while True:
        code = ''.join(random.choices(string.digits, k=3))
        # Check both in-memory and database
        if code not in active_sessions and not GameSession.query.filter_by(code=code).first():
            return code

# Serve the HTML page
@app.route('/')
def index():
    return render_template('index.html')

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# API Routes
@app.route('/api/create_session', methods=['POST'])
def create_session():
    data = request.json
    student_name = data.get('name', 'Student 1')
    
    session_code = generate_session_code()
    
    # Create database entry
    game_session = GameSession(
        code=session_code,
        student1_name=student_name,
        status='waiting'
    )
    db.session.add(game_session)
    db.session.commit()
    
    # Generate per-session questions using AI (personalized for student1)
    try:
        generated = generate_questions(student_name, None, count=10)
        session_questions = generated if isinstance(generated, list) and len(generated) > 0 else questions
    except Exception:
        session_questions = questions

    # Also maintain in-memory for compatibility
    active_sessions[session_code] = {
        'student1': {
            'name': student_name,
            'answers': [],
            'score': 0
        },
        'student2': {
            'name': '',
            'answers': [],
            'score': 0
        },
        'status': 'waiting',  # waiting, in_progress, completed
        'current_question': 0,
        'questions': session_questions,
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({
        'session_code': session_code,
        'session_data': active_sessions[session_code]
    })

@app.route('/api/join_session', methods=['POST'])
def join_session():
    data = request.json
    session_code = data.get('session_code')
    student_name = data.get('name', 'Student 2')
    
    # Check database first
    game_session_db = GameSession.query.filter_by(code=session_code).first()
    if not game_session_db:
        return jsonify({'error': 'Invalid session code'}), 404
    
    if game_session_db.student2_name:
        return jsonify({'error': 'Session is full'}), 400
    
    # Update database
    game_session_db.student2_name = student_name
    game_session_db.status = 'in_progress'
    db.session.commit()
    
    # Also update in-memory storage
    if session_code not in active_sessions:
        return jsonify({'error': 'Session not found in memory'}), 404
    
    game_session = active_sessions[session_code]
    game_session['student2']['name'] = student_name
    game_session['status'] = 'in_progress'

    # Optionally regenerate questions personalized with both names before the game progresses
    try:
        regenerated = generate_questions(game_session['student1']['name'], student_name, count=10)
        if isinstance(regenerated, list) and len(regenerated) == len(game_session['questions']):
            game_session['questions'] = regenerated
    except Exception:
        pass
    
    return jsonify({
        'session_code': session_code,
        'session_data': game_session
    })

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    session_code = data.get('session_code')
    student_number = data.get('student_number')  # 1 or 2
    answer = data.get('answer')  # 1 or 2
    
    if not session_code or session_code not in active_sessions:
        return jsonify({'error': 'Invalid session code'}), 404
    
    if student_number not in [1, 2]:
        return jsonify({'error': 'Invalid student number'}), 400
    
    if answer not in [1, 2]:
        return jsonify({'error': 'Invalid answer'}), 400
    
    # Get database session
    game_session_db = GameSession.query.filter_by(code=session_code).first()
    if not game_session_db:
        return jsonify({'error': 'Session not found in database'}), 404
    
    game_session = active_sessions[session_code]
    
    # Record answer
    student_key = f'student{student_number}'
    game_session[student_key]['answers'].append(answer)
    
    # Update database with answers
    if student_number == 1:
        game_session_db.set_student1_answers(game_session['student1']['answers'])
    else:
        game_session_db.set_student2_answers(game_session['student2']['answers'])
    
    # Check if both students have answered all questions
    student1_complete = len(game_session['student1']['answers']) == len(questions)
    student2_complete = len(game_session['student2']['answers']) == len(questions)
    
    # If both students have completed all questions, calculate scores
    if student1_complete and student2_complete:
        # Calculate matching answers
        matching_answers = 0
        for i in range(len(questions)):
            if game_session['student1']['answers'][i] == game_session['student2']['answers'][i]:
                matching_answers += 1
        
        # Calculate scores (10 points per matching answer)
        score = matching_answers * 10
        game_session['student1']['score'] = score
        game_session['student2']['score'] = score
        
        # Update game status
        game_session['status'] = 'completed'
        
        # Update database
        game_session_db.student1_score = score
        game_session_db.student2_score = score
        game_session_db.status = 'completed'
        
        # Add to leaderboard database
        leaderboard_entry = LeaderboardEntry(
            student1_name=game_session['student1']['name'],
            student2_name=game_session['student2']['name'],
            matching_answers=matching_answers,
            score=score
        )
        db.session.add(leaderboard_entry)
    
    # Commit all database changes
    db.session.commit()
    
    return jsonify({
        'session_code': session_code,
        'session_data': game_session
    })

@app.route('/api/get_session', methods=['GET'])
def get_session():
    session_code = request.args.get('session_code')
    
    if not session_code or session_code not in active_sessions:
        return jsonify({'error': 'Invalid session code'}), 404
    
    return jsonify(active_sessions[session_code])

@app.route('/api/get_leaderboard', methods=['GET'])
def get_leaderboard():
    # Get leaderboard from database
    entries = LeaderboardEntry.query.order_by(LeaderboardEntry.score.desc()).limit(10).all()
    
    leaderboard_data = []
    for entry in entries:
        leaderboard_data.append({
            'student1': entry.student1_name,
            'student2': entry.student2_name,
            'matching_answers': entry.matching_answers,
            'score': entry.score,
            'date': entry.date.strftime('%m/%d/%Y')
        })
    
    return jsonify(leaderboard_data)

if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")
    
    print("Starting Flask application...")
    print("Access the application at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
