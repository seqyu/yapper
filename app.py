from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import sqlite3
import os
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

# Database setup
DATABASE = 'yapper.db'
blocked_usernames = ['Bot']
reset_thread_started = False  # Track if the reset thread has been started
reset_interval = None  # Global variable to store reset interval

def init_db():
    if not os.path.exists(DATABASE):
        reset_database()

def reset_database():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS posts')
        cursor.execute('''
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    print("Database reset.")

# Function to read announcement from file
def get_motd():
    try:
        with open('motd.txt', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return ''

def get_ver():
    try:
        with open('version', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return 'NaN'

def get_name():
    try:
        with open('name', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return 'yapper instance'
def get_rules():
    try:
        with open('rules', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return 'ANARCHY MODE!\nThis server has no rules! Just remember to follow the law!'

def load_reset_interval():
    """Load the reset interval from a file or use a default value."""
    global reset_interval
    try:
        with open('resettime.txt', 'r') as file:
            reset_interval = int(file.read().strip()) * 3600  # Convert hours to seconds
            print(f"This instance will delete the pavés every {reset_interval // 3600} hours.")
    except (FileNotFoundError, ValueError):
        reset_interval = 24 * 3600  # Default to 24 hours
        print("resettime.txt not found or invalid. This instance will delete the pavés every 24 hours.")

def database_reset_thread():
    global reset_thread_started
    if reset_thread_started:
        return
    reset_thread_started = True

    while True:
        print(f"Waiting {reset_interval // 3600} hours to reset the database...")
        time.sleep(reset_interval)
        reset_database()
        print("Database reset triggered.")

@app.route('/')
def index():
    motd = get_motd()
    version = get_ver()
    rules = get_rules()
    name = get_name()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, content, timestamp FROM posts ORDER BY timestamp DESC')
        posts = cursor.fetchall()
    return render_template('index.html', posts=posts, motd=motd, version=version, rules=rules, name=name)

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

def start_app():
    init_db()
    load_reset_interval()  # Load reset interval once
    # Start the database reset thread
    reset_thread = threading.Thread(target=database_reset_thread, daemon=True)
    reset_thread.start()
    print(f"Welcome to {get_ver()}!")
    print("Message Of The Day:")
    print(get_motd())
    print("Server name:")
    print(get_name())
if __name__ == '__main__':
    start_app()
    socketio.run(app, debug=True, use_reloader=False)
