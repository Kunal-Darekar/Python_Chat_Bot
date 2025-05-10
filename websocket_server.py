from flask_socketio import SocketIO, emit, join_room, leave_room, request
import json
from datetime import datetime

# Initialize SocketIO
socketio = SocketIO()

# Connected users tracking
connected_users = {}

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    socketio.init_app(app, cors_allowed_origins="*")
    register_handlers()
    return socketio

def register_handlers():
    """Register all WebSocket event handlers"""

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f"Client connected: {request.sid}")

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        # Remove user from all rooms
        if request.sid in connected_users:
            username = connected_users[request.sid]['username']
            rooms = connected_users[request.sid]['rooms'].copy()

            for room_name in rooms:
                leave_chat_room(username, room_name)

            # Remove from connected users
            del connected_users[request.sid]

            # Broadcast user offline status
            socketio.emit('user_status', {
                'username': username,
                'status': 'offline',
                'timestamp': datetime.now().isoformat()
            })

            print(f"Client disconnected: {request.sid} ({username})")

    @socketio.on('authenticate')
    def handle_authenticate(data):
        """Handle user authentication"""
        username = data.get('username')

        if not username:
            emit('error', {'message': 'Username is required'})
            return

        # Store user information
        connected_users[request.sid] = {
            'username': username,
            'rooms': set(),
            'status': 'online',
            'last_activity': datetime.now().isoformat()
        }

        # Broadcast user online status
        socketio.emit('user_status', {
            'username': username,
            'status': 'online',
            'timestamp': datetime.now().isoformat()
        })

        emit('authenticated', {'username': username, 'status': 'success'})
        print(f"User authenticated: {username}")

    @socketio.on('join_room')
    def handle_join_room(data):
        """Handle user joining a chat room"""
        if request.sid not in connected_users:
            emit('error', {'message': 'Not authenticated'})
            return

        username = connected_users[request.sid]['username']
        room_name = data.get('room')

        if not room_name:
            emit('error', {'message': 'Room name is required'})
            return

        # Join the room
        join_room(room_name)
        connected_users[request.sid]['rooms'].add(room_name)

        # Notify room about new user
        emit('user_joined', {
            'username': username,
            'room': room_name,
            'timestamp': datetime.now().isoformat()
        }, room=room_name)

        print(f"User {username} joined room: {room_name}")

    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Handle user leaving a chat room"""
        if request.sid not in connected_users:
            emit('error', {'message': 'Not authenticated'})
            return

        username = connected_users[request.sid]['username']
        room_name = data.get('room')

        if not room_name:
            emit('error', {'message': 'Room name is required'})
            return

        # Leave the room
        leave_chat_room(username, room_name)

    @socketio.on('new_message')
    def handle_new_message(data):
        """Handle new chat message"""
        if request.sid not in connected_users:
            emit('error', {'message': 'Not authenticated'})
            return

        username = connected_users[request.sid]['username']
        room_name = data.get('room')
        message = data.get('message', '').strip()

        if not room_name or not message:
            emit('error', {'message': 'Room name and message are required'})
            return

        # Check if user is in the room
        if room_name not in connected_users[request.sid]['rooms']:
            emit('error', {'message': 'You are not in this room'})
            return

        # Update last activity
        connected_users[request.sid]['last_activity'] = datetime.now().isoformat()

        # Broadcast message to room (will be saved to database by the API endpoint)
        # This is just for real-time delivery
        emit('chat_message', {
            'username': username,
            'room': room_name,
            'message': message,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, room=room_name)

    @socketio.on('typing')
    def handle_typing(data):
        """Handle typing indicator"""
        if request.sid not in connected_users:
            return

        username = connected_users[request.sid]['username']
        room_name = data.get('room')
        is_typing = data.get('typing', False)

        if not room_name:
            return

        # Check if user is in the room
        if room_name not in connected_users[request.sid]['rooms']:
            return

        # Broadcast typing status to room
        emit('user_typing', {
            'username': username,
            'room': room_name,
            'typing': is_typing
        }, room=room_name, include_self=False)

def leave_chat_room(username, room_name):
    """Helper function to leave a chat room"""
    # Find user's session ID
    session_id = None
    for sid, data in connected_users.items():
        if data['username'] == username and room_name in data['rooms']:
            session_id = sid
            break

    if not session_id:
        return

    # Leave the room
    leave_room(room_name, sid=session_id)
    connected_users[session_id]['rooms'].remove(room_name)

    # Notify room about user leaving
    socketio.emit('user_left', {
        'username': username,
        'room': room_name,
        'timestamp': datetime.now().isoformat()
    }, room=room_name)

    print(f"User {username} left room: {room_name}")

def broadcast_to_room(room_name, event, data):
    """Broadcast an event to all users in a room"""
    socketio.emit(event, data, room=room_name)

def broadcast_to_user(username, event, data):
    """Broadcast an event to a specific user"""
    # Find user's session ID
    for sid, user_data in connected_users.items():
        if user_data['username'] == username:
            socketio.emit(event, data, room=sid)
            return True
    return False

def get_online_users():
    """Get list of online users"""
    online_users = {}
    for sid, data in connected_users.items():
        username = data['username']
        online_users[username] = {
            'status': data['status'],
            'last_activity': data['last_activity'],
            'rooms': list(data['rooms'])
        }
    return online_users

def get_room_users(room_name):
    """Get list of users in a room"""
    room_users = []
    for sid, data in connected_users.items():
        if room_name in data['rooms']:
            room_users.append(data['username'])
    return room_users
