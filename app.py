import os
from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__, template_folder='frontend')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    send({'text': f"{data['username']} has joined the room {room}", 'username': 'INFO'}, to=room)

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    leave_room(room)
    send({'text': f"{data['username']} has left the room {room}", 'username': 'INFO'}, to=room)

@socketio.on('message')
def handle_message(msg):
    room = msg['room']
    send({'text': msg['text'], 'username': msg['username']}, to=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    env = os.environ.get('ENV', 'production')
    if env == 'local':
        socketio.run(app, host='127.0.0.1', port=port, debug=True)
    else:
        socketio.run(app, host='0.0.0.0', port=port)