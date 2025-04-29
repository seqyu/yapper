from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect
import sqlite3
import os
import threading
import time
import re

app = Flask(__name__)
socketio = SocketIO(app)

DATABASE = 'yapper.db'
CONFIG_FILE = 'yapper.properties'
config = {}
reset_thread_started = False
reset_interval = 24 * 3600
active_users = set()
banned_words = set()

def load_properties():
    global config
    config = {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, val = line.split('=', 1)
                        config[key.strip()] = val.strip()
    except FileNotFoundError:
        print("Warning: yapper.properties not found. Using default settings.")

def load_banned_words():
    path = config.get('banned_words_file', 'banned_words.txt')
    try:
        with open(path, 'r') as f:
            return {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        print(f"Warning: {path} not found. No words will be filtered.")
        return set()

def violates_rules(content):
    lowered = content.lower()
    if any(bad_word in lowered for bad_word in banned_words):
        return "Your message contains banned words."
    if re.search(r'(.)\1{10,}', content):
        return "Your message contains excessive repeated characters."
    if len(content) > 200:
        return "Your message is too long."
    return None

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

@app.route('/old')
def indexold():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, content, timestamp FROM posts ORDER BY timestamp DESC')
        posts = cursor.fetchall()
    return render_template('index.html', posts=posts,
                           motd=config.get('motd', ''),
                           version=config.get('version', 'NaN'),
                           rules=config.get('rules', ''),
                           name=config.get('name', 'A yapper instance'))

@app.route('/')
def index():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, content, timestamp FROM posts ORDER BY timestamp DESC')
        posts = cursor.fetchall()
    return render_template('indexnew.html', posts=posts,
                           motd=config.get('motd', ''),
                           version=config.get('version', 'NaN'),
                           rules=config.get('rules', ''),
                           name=config.get('name', 'A yapper instance'))

@socketio.on('new_post')
def handle_new_post(data):
    global banned_words
    banned_words = load_banned_words()  # Reload each time

    username = data.get('username', 'Anonymous')
    content = data.get('content')

    if content and content.strip():
        rule_violation = violates_rules(content)
        if rule_violation:
            print(f"[AUTOMOD BLOCKED] {username}: {rule_violation}")
            emit('post_blocked', {'message': rule_violation})
            return

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO posts (username, content) VALUES (?, ?)', (username, content))
            conn.commit()
        emit('broadcast_post', {'username': username, 'content': content}, broadcast=True)

@socketio.on('connect')
def handle_connect():
    active_users.add(request.sid)
    emit('online_count', {'count': len(active_users)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    active_users.discard(request.sid)
    emit('online_count', {'count': len(active_users)}, broadcast=True)

def start_app():
    global reset_interval, banned_words
    load_properties()
    reset_hours = int(config.get('reset_interval_hours', '24'))
    reset_interval = reset_hours * 3600
    banned_words = load_banned_words()
    init_db()

    print(f"Welcome to version {config.get('version', 'NaN')}!")
    print("Message Of The Day:")
    print(config.get('motd', ''))
    print("Server name:")
    print(config.get('name', 'Yapper'))

    threading.Thread(target=database_reset_thread, daemon=True).start()

if __name__ == '__main__':
    start_app()
    socketio.run(app, host="0.0.0.0", port=5050, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
