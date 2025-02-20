import os
import random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, send
import time

app = Flask(__name__, template_folder='frontend')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lobby')
def lobby():
    return render_template('lobby.html')

def generate_unique_room_id():
    while True:
        room_id = str(random.randint(1000, 9999))
        if room_id not in rooms:
            rooms[room_id] = 1
            return room_id

@socketio.on('joinRoom')
def handle_joinRoom(data):
    username = data['username']
    room = data['room']
    if room not in rooms:
        socketio.emit('roomNotFound', {'room': room})
        return
    rooms[room] += 1
    join_room(room)
    socketio.emit('roomJoined', {'room': room, 'username': username}, room=request.sid)
    time.sleep(0.5)
    socketio.emit('players', {'players': rooms[room]})
    
@socketio.on('createRoom')
def handle_createRoom(data):
    username = data['username']
    room = generate_unique_room_id()
    join_room(room)
    socketio.emit('roomJoined', {'room': room, 'username': username}, room=request.sid)
    time.sleep(0.5)
    socketio.emit('players', {'players': rooms[room]})

@socketio.on('leaveRoom')
def handle_leaveRoom(data):
    username = data['username']
    room = data['room']
    rooms[room] -= 1
    leave_room(room)
    socketio.emit('players', {'players': rooms[room]})
    socketio.emit('roomLeft', {'room': room, 'username': username}, room=request.sid)
    if rooms[room] <= 0:
        del rooms[room]



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    env = os.environ.get('ENV', 'production')
    if env == 'local':
        socketio.run(app, host='127.0.0.1', port=port, debug=True)
    else:
        socketio.run(app, host='0.0.0.0', port=port)