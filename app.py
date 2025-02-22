import os
import random
import requests
import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room

app = Flask(__name__, template_folder='frontend')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lobby')
def lobby():
    return render_template('lobby.html')

@app.route('/createMeme')
def createMeme():
    return render_template('createMeme.html')

## ROOM VARIABLES
roomsReady = {} # {'8241': [{'username': 'fdsa', 'ready': False}], '2882': []}
roomsPlaying = {} # {'8241': template, '2882': templates} Rooms actively playing as key, and all templates shuffled

## CREATE ROOM
def generate_unique_room_id():
    while True:
        room_id = str(random.randint(1000, 9999))
        if room_id not in roomsReady:
            roomsReady[room_id] = []
            return room_id
        
@socketio.on('createRoom')
def createRoom(data):
    room = generate_unique_room_id()
    username = data['username']
    roomsReady[room].append({'username': username, 'ready': False})
    join_room(room)
    socketio.emit('joinedRoom', {'room': room, 'username': username}, to=request.sid)

## JOIN ROOM
# check if username is taken
def is_username_taken(username, room):
    for user in roomsReady[room]:
        if user['username'] == username:
            return True
    return False

@socketio.on('joinRoom')
def joinRoom(data):
    room = data['room']
    username = data['username']
    if room not in roomsReady:
        socketio.emit('roomError', {'room': room, 'error': 'Room not found!'}, to=request.sid)
        return
    if is_username_taken(username, room):
        socketio.emit('roomError', {'room': room, 'error': 'Username already taken!'}, to=request.sid)
        return
    roomsReady[room].append({'username': username, 'ready': False})
    join_room(room)
    socketio.emit('joinedRoom', {'room': room, 'username': username}, to=request.sid)
    socketio.emit('updateRoom', {'room': room, 'roomsReady': roomsReady[room]},to=room)

## ASK UPDATE ROOM
@socketio.on('askUpdateRoom')
def askUpdateRoom(data):
    join_room(data['room'])
    room = data['room']
    socketio.emit('updateRoom', {'room': room, 'roomsReady': roomsReady[room]}, to=room)

## LEAVE ROOM CHECK TO DELETE
@socketio.on('leaveRoom')
def leaveRoom(data):
    room = data['room']
    username = data['username']
    roomsReady[room] = [player for player in roomsReady[room] if player['username'] != username]
    socketio.emit('updateRoom', {'room': room, 'roomsReady': roomsReady[room]}, to=room)
    leave_room(room)

## START
@socketio.on('getTemplate')
def getTemplate(data):
    print('getTemplate')
    room = data['room']
    socketio.emit('sendTemplate', {'room': room, 'templates': roomsPlaying[room][0]}, to=request.sid)

## PULL TEMPLATES FROM API
def getTemplates(room):
    response = requests.get('https://api.imgflip.com/get_memes')
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            memes = data['data']['memes']
            random.shuffle(memes)  # Shuffle the list of memes
            roomsPlaying[room] = memes  # Store the shuffled list in roomsPlaying
            socketio.emit('startGame', {'room': room}, to=room)
        else:
            print("Failed to retrieve memes: API response was not successful")
    else:
        print(f"Failed to retrieve memes: HTTP {response.status_code}")

## SET READY
@socketio.on('setReady')
def setReady(data):
    room = data['room']
    username = data['username']
    for player in roomsReady[room]:
        if player['username'] == username:
            player['ready'] = not player['ready']
    socketio.emit('updateRoom', {'room': room, 'roomsReady': roomsReady[room]}, to=room)
    if len(roomsReady[room]) >= 3 and all([player['ready'] for player in roomsReady[room]]):
        getTemplates(room)



## CREATE MEME

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    env = os.environ.get('ENV', 'production')
    if env == 'local':
        socketio.run(app, host='127.0.0.1', port=port, debug=True)
    else:
        socketio.run(app, host='0.0.0.0', port=port)