from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import random
import string
import os
import json
from datetime import datetime
from open_ai.ai import generate_questions
import uuid

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'quiz_game.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GameSession(db.Model):
    code = db.Column(db.String(3), primary_key=True)
    student1_name = db.Column(db.String(100), nullable=False)
    student2_name = db.Column(db.String(100), nullable=True)
    student1_answers = db.Column(db.Text, default='[]')
    student2_answers = db.Column(db.Text, default='[]')
    student1_score = db.Column(db.Integer, default=0)
    student2_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='waiting')
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

active_sessions = {}

questions = [
    {"question": "Would you rather...", "option1": "Copy someone else's homework the morning it's due", "option2": "Pay someone to write your final paper"},
    {"question": "Would you rather...", "option1": "Take an exam you didn't study for honestly", "option2": "Cheat but risk getting caught and failing the course"},
    {"question": "Would you rather...", "option1": "Work with a friend on an assignment meant to be individual", "option2": "Turn in an assignment late and lose points"},
    {"question": "Would you rather...", "option1": "Use ChatGPT to write your entire essay", "option2": "Submit a poorly written essay you actually wrote"},
    {"question": "Would you rather...", "option1": "Let a classmate copy your work knowing they'll keep doing it", "option2": "Refuse to share and risk the friendship"},
    {"question": "Would you rather...", "option1": "Take credit for a group project you barely contributed to", "option2": "Tell the professor you didn't do your fair share"},
    {"question": "Would you rather...", "option1": "Use a fake excuse to get an extension", "option2": "Submit incomplete work on time"},
    {"question": "Would you rather...", "option1": "Have your professor discover you plagiarized", "option2": "Never get caught but always know you cheated"},
    {"question": "Would you rather...", "option1": "Share test questions with friends after taking an exam", "option2": "Keep them to yourself knowing others might fail"},
    {"question": "Would you rather...", "option1": "Get an A by cheating in one important course", "option2": "Get a B by being honest in all your courses"}
]

def generate_session_code():
    while True:
        code = ''.join(random.choices(string.digits, k=3))
        if code not in active_sessions and not GameSession.query.filter_by(code=code).first():
            return code

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create_session', methods=['POST'])
def create_session():
    data = request.json
    student_name = data.get('name', 'Student 1')
    
    session_code = generate_session_code()
    
    game_session = GameSession(
        code=session_code,
        student1_name=student_name,
        status='waiting'
    )
    db.session.add(game_session)
    db.session.commit()
    
    try:
        generated = generate_questions(student_name, None, count=10)
        session_questions = generated if isinstance(generated, list) and len(generated) > 0 else questions
    except Exception:
        session_questions = questions

    active_sessions[session_code] = {
        'student1': {'name': student_name, 'answers': [], 'score': 0},
        'student2': {'name': '', 'answers': [], 'score': 0},
        'status': 'waiting',
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
    
    game_session_db = GameSession.query.filter_by(code=session_code).first()
    if not game_session_db:
        return jsonify({'error': 'Invalid session code'}), 404
    
    if game_session_db.student2_name:
        return jsonify({'error': 'Session is full'}), 400
    
    game_session_db.student2_name = student_name
    game_session_db.status = 'in_progress'
    db.session.commit()
    
    if session_code not in active_sessions:
        session_data = {
            'student1': {
                'name': game_session_db.student1_name,
                'answers': game_session_db.get_student1_answers(),
                'score': game_session_db.student1_score
            },
            'student2': {
                'name': student_name,
                'answers': game_session_db.get_student2_answers(),
                'score': game_session_db.student2_score
            },
            'status': 'in_progress',
            'current_question': game_session_db.current_question,
            'questions': questions,
            'created_at': game_session_db.created_at.isoformat() if game_session_db.created_at else datetime.now().isoformat()
        }
        active_sessions[session_code] = session_data
    else:
        game_session = active_sessions[session_code]
        game_session['student2']['name'] = student_name
        game_session['status'] = 'in_progress'

    game_session = active_sessions[session_code]

    if 'questions' not in game_session or len(game_session.get('questions', [])) == 0 or game_session.get('questions') == questions:
        try:
            regenerated = generate_questions(game_session['student1']['name'], student_name, count=10)
            if isinstance(regenerated, list) and len(regenerated) >= 10:
                game_session['questions'] = regenerated[:10]
            else:
                game_session['questions'] = questions[:10]
        except Exception as e:
            print(f"Error regenerating questions: {e}")
            game_session['questions'] = questions[:10]
    
    if len(game_session.get('questions', [])) != 10:
        game_session['questions'] = questions[:10]
    
    return jsonify({
        'session_code': session_code,
        'session_data': game_session
    })

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    session_code = data.get('session_code')
    student_number = data.get('student_number')
    answer = data.get('answer')
    
    if not session_code:
        return jsonify({'error': 'Invalid session code'}), 404
    
    if student_number not in [1, 2]:
        return jsonify({'error': 'Invalid student number'}), 400
    
    if answer not in [1, 2]:
        return jsonify({'error': 'Invalid answer'}), 400
    
    game_session_db = GameSession.query.filter_by(code=session_code).first()
    if not game_session_db:
        return jsonify({'error': 'Session not found in database'}), 404
    
    if session_code not in active_sessions:
        session_questions = questions[:10]
        if game_session_db.student2_name:
            try:
                generated = generate_questions(game_session_db.student1_name, game_session_db.student2_name, count=10)
                if isinstance(generated, list) and len(generated) >= 10:
                    session_questions = generated[:10]
            except Exception:
                pass
        
        session_data = {
            'student1': {
                'name': game_session_db.student1_name,
                'answers': game_session_db.get_student1_answers(),
                'score': game_session_db.student1_score
            },
            'student2': {
                'name': game_session_db.student2_name or '',
                'answers': game_session_db.get_student2_answers(),
                'score': game_session_db.student2_score
            },
            'status': game_session_db.status,
            'current_question': game_session_db.current_question,
            'questions': session_questions,
            'created_at': game_session_db.created_at.isoformat() if game_session_db.created_at else datetime.now().isoformat()
        }
        active_sessions[session_code] = session_data
    else:
        if 'questions' not in active_sessions[session_code] or len(active_sessions[session_code].get('questions', [])) != 10:
            if game_session_db.student2_name:
                try:
                    generated = generate_questions(game_session_db.student1_name, game_session_db.student2_name, count=10)
                    if isinstance(generated, list) and len(generated) >= 10:
                        active_sessions[session_code]['questions'] = generated[:10]
                    else:
                        active_sessions[session_code]['questions'] = questions[:10]
                except Exception:
                    active_sessions[session_code]['questions'] = questions[:10]
            else:
                active_sessions[session_code]['questions'] = questions[:10]
    
    game_session = active_sessions[session_code]
    
    student_key = f'student{student_number}'
    total_q = len(game_session.get('questions', questions))
    current_answer_count = len(game_session[student_key]['answers'])
    
    if current_answer_count >= total_q:
        return jsonify({
            'session_code': session_code,
            'session_data': game_session,
            'message': 'All questions already answered'
        })
    
    game_session[student_key]['answers'].append(answer)
    
    if student_number == 1:
        game_session_db.set_student1_answers(game_session['student1']['answers'])
        game_session_db.current_question = max(game_session_db.current_question, current_answer_count)
    else:
        game_session_db.set_student2_answers(game_session['student2']['answers'])
        game_session_db.current_question = max(game_session_db.current_question, current_answer_count)
    
    student1_complete = len(game_session['student1']['answers']) == total_q
    student2_complete = len(game_session['student2']['answers']) == total_q
    
    if student1_complete and student2_complete and game_session_db.status != 'completed':
        matching_answers = 0
        for i in range(total_q):
            if game_session['student1']['answers'][i] == game_session['student2']['answers'][i]:
                matching_answers += 1
        
        score = matching_answers * 10
        game_session['student1']['score'] = score
        game_session['student2']['score'] = score
        game_session['status'] = 'completed'
        
        game_session_db.student1_score = score
        game_session_db.student2_score = score
        game_session_db.status = 'completed'
        
        existing_entry = LeaderboardEntry.query.filter_by(
            student1_name=game_session['student1']['name'],
            student2_name=game_session['student2']['name']
        ).first()
        
        if not existing_entry:
            leaderboard_entry = LeaderboardEntry(
                student1_name=game_session['student1']['name'],
                student2_name=game_session['student2']['name'],
                matching_answers=matching_answers,
                score=score
            )
            db.session.add(leaderboard_entry)
    
    db.session.commit()
    
    return jsonify({
        'session_code': session_code,
        'session_data': game_session
    })

@app.route('/api/get_session', methods=['GET'])
def get_session():
    session_code = request.args.get('session_code')
    
    if not session_code:
        return jsonify({'error': 'Invalid session code'}), 404
    
    game_session_db = GameSession.query.filter_by(code=session_code).first()
    if not game_session_db:
        return jsonify({'error': 'Session not found'}), 404
    
    if session_code not in active_sessions:
        session_questions = questions[:10]
        if game_session_db.student2_name:
            try:
                generated = generate_questions(game_session_db.student1_name, game_session_db.student2_name, count=10)
                if isinstance(generated, list) and len(generated) >= 10:
                    session_questions = generated[:10]
            except Exception:
                pass
        
        session_data = {
            'student1': {
                'name': game_session_db.student1_name,
                'answers': game_session_db.get_student1_answers(),
                'score': game_session_db.student1_score
            },
            'student2': {
                'name': game_session_db.student2_name or '',
                'answers': game_session_db.get_student2_answers(),
                'score': game_session_db.student2_score
            },
            'status': game_session_db.status,
            'current_question': game_session_db.current_question,
            'questions': session_questions,
            'created_at': game_session_db.created_at.isoformat() if game_session_db.created_at else datetime.now().isoformat()
        }
        active_sessions[session_code] = session_data
    else:
        game_session = active_sessions[session_code]
        game_session['student1']['answers'] = game_session_db.get_student1_answers()
        game_session['student2']['answers'] = game_session_db.get_student2_answers()
        game_session['student1']['score'] = game_session_db.student1_score
        game_session['student2']['score'] = game_session_db.student2_score
        game_session['status'] = game_session_db.status
        game_session['current_question'] = game_session_db.current_question
        
        if 'questions' not in game_session or len(game_session.get('questions', [])) != 10:
            if game_session_db.student2_name:
                try:
                    generated = generate_questions(game_session_db.student1_name, game_session_db.student2_name, count=10)
                    if isinstance(generated, list) and len(generated) >= 10:
                        game_session['questions'] = generated[:10]
                    else:
                        game_session['questions'] = questions[:10]
                except Exception:
                    game_session['questions'] = questions[:10]
            else:
                game_session['questions'] = questions[:10]
    
    return jsonify(active_sessions[session_code])

@app.route('/api/get_leaderboard', methods=['GET'])
def get_leaderboard():
    entries = LeaderboardEntry.query.order_by(LeaderboardEntry.score.desc()).all()
    
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
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
