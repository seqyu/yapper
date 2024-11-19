from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import sqlite3
import os

app = Flask(__name__)
socketio = SocketIO(app)

# Database setup
DATABASE = 'yapper.db'

blocked_usernames = ['Bot']

def init_db():
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        print("Database initialized.")

# Function to read announcement from file
def get_announcement():
    try:
        with open('announcement.txt', 'r') as file:
            return file.read().strip()  # Remove extra whitespace
    except FileNotFoundError:
        return ''  # Return empty string if no announcement file is found

def get_ver():
    try:
        with open('version', 'r') as file:
            return file.read().strip()  # Remove extra whitespace
    except FileNotFoundError:
        return ''  # Return empty string if no announcement file is found
def get_rules():
    try:
        with open('rules', 'r') as file:
            return file.read().strip()  # Remove extra whitespace
    except FileNotFoundError:
        return 'ANARCHY MODE!\nThis server has no rules! Just remember to follow the law!'  # Return empty string if no announcement file is found
@app.route('/')
def index():
    announcement = get_announcement()  # Get the announcement content
    version = get_ver()
    rules = get_rules()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, content, timestamp FROM posts ORDER BY timestamp DESC')
        posts = cursor.fetchall()
    return render_template('index.html', posts=posts, announcement=announcement, version=version, rules=rules)

@socketio.on('new_post')
def handle_new_post(data):
    username = data.get('username', 'Anonymous')
    content = data.get('content')
    
    # Check if username is blocked
    if username in blocked_usernames:
        emit('post_blocked', {'message': 'Your username is blocked from posting.'})
        return
    
    # Ensure content is not empty
    if content and content.strip():
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO posts (username, content) VALUES (?, ?)', (username, content))
            conn.commit()
        emit('broadcast_post', {'username': username, 'content': content}, broadcast=True)

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True)
