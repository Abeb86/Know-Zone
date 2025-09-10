"""
This file demonstrates how to integrate the Flask backend with the frontend.
You would need to modify your HTML/JS code to use these API endpoints instead of localStorage.
"""

import requests
import socketio

# Base URL for the API
BASE_URL = 'http://localhost:5000/api'

# Initialize Socket.IO client
sio = socketio.Client()

# Socket.IO event handlers
@sio.event
def connect():
    print('Connected to server')

@sio.event
def disconnect():
    print('Disconnected from server')

@sio.on('game_started')
def on_game_started(data):
    print('Game started:', data)

@sio.on('next_question')
def on_next_question(data):
    print('Next question:', data)

@sio.on('game_completed')
def on_game_completed(data):
    print('Game completed:', data)

@sio.on('user_joined')
def on_user_joined(data):
    print('User joined:', data)

@sio.on('user_left')
def on_user_left(data):
    print('User left:', data)

# Example usage
def example_flow():
    # 1. Login
    login_response = requests.post(f'{BASE_URL}/login', json={
        'username': 'Player1'
    })
    login_data = login_response.json()
    print('Login response:', login_data)
    
    # Get cookies from login response
    cookies = login_response.cookies
    
    # 2. Create a session
    create_session_response = requests.post(
        f'{BASE_URL}/create_session', 
        cookies=cookies
    )
    session_data = create_session_response.json()
    session_code = session_data['session_code']
    print('Created session:', session_data)
    
    # 3. Connect to Socket.IO
    sio.connect('http://localhost:5000')
    
    # 4. Join the room
    sio.emit('join', {'session_code': session_code})
    
    # 5. Start the session (as host)
    start_session_response = requests.post(
        f'{BASE_URL}/start_session',
        json={'session_code': session_code},
        cookies=cookies
    )
    print('Started session:', start_session_response.json())
    
    # 6. Submit an answer
    submit_answer_response = requests.post(
        f'{BASE_URL}/submit_answer',
        json={
            'session_code': session_code,
            'answer': 1  # Option 1
        },
        cookies=cookies
    )
    print('Submitted answer:', submit_answer_response.json())
    
    # 7. Get leaderboard
    leaderboard_response = requests.get(f'{BASE_URL}/get_leaderboard')
    print('Leaderboard:', leaderboard_response.json())
    
    # 8. Disconnect from Socket.IO
    sio.disconnect()
    
    # 9. Logout
    logout_response = requests.post(f'{BASE_URL}/logout', cookies=cookies)
    print('Logout response:', logout_response.json())

if __name__ == '__main__':
    print("This is an example client integration. Run the Flask server first.")
    print("To test the actual flow, you would need to modify your frontend code.")
