from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import time
import json
import secrets
import threading
from datetime import datetime
from dotenv import load_dotenv
from mongodb_connector import MongoDBConnector

# Import WebSocket support
try:
    from websocket_server import init_socketio, socketio, broadcast_to_room
    WEBSOCKET_ENABLED = True
    print("WebSocket support enabled")
except ImportError:
    WEBSOCKET_ENABLED = False
    print("WebSocket support not available")

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(16))

# Initialize WebSockets if available
if WEBSOCKET_ENABLED:
    socketio = init_socketio(app)

# Create database instance
try:
    db = MongoDBConnector()

    # Migrate data from files to MongoDB if needed
    try:
        # Check if this is the first run with MongoDB by checking if the migration_completed flag is set
        migration_completed = db.ai_data.find_one({"type": "migration_completed"})
        if not migration_completed:
            print("First run with MongoDB detected. Migrating data from files...")
            db.migrate_from_files()
            # Set migration_completed flag
            db.ai_data.insert_one({"type": "migration_completed", "timestamp": datetime.now().isoformat()})
    except Exception as e:
        print(f"Error during migration: {e}")

    USING_MONGODB = True
    print("Using MongoDB for data storage")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    print("Falling back to file-based storage")
    try:
        from Database import Database
        db = Database()
    except ImportError:
        # Create a simple file-based database fallback
        class SimpleFileDatabase:
            def __init__(self):
                self.data_dir = "data"
                os.makedirs(self.data_dir, exist_ok=True)

            def load_user_data(self, username):
                """Load user data from file"""
                user_file = os.path.join(self.data_dir, f"user_{username}.json")
                if os.path.exists(user_file):
                    try:
                        with open(user_file, 'r') as f:
                            return json.load(f)
                    except:
                        pass
                return {"username": username, "email": "", "joined_rooms": [], "messages_sent": 0}

            def save_user_data(self, username, data):
                """Save user data to file"""
                user_file = os.path.join(self.data_dir, f"user_{username}.json")
                with open(user_file, 'w') as f:
                    json.dump(data, f)

            def get_room_metadata(self, room_name):
                """Get room metadata"""
                return {"name": room_name, "description": "", "active_users": []}

            def update_room_metadata(self, room_name, metadata):
                """Update room metadata"""
                pass

            def get_room_messages(self, room_name, limit=50):
                """Get messages from a room"""
                return []

            def add_message_to_room(self, room_name, username, message, sentiment=None):
                """Add a message to a room"""
                return True

            def get_active_rooms(self, limit=50):
                """Get active rooms"""
                return []

            def load_room_data(self):
                """Load room data"""
                return {}

            def save_room_data(self, room_name, password, description="", tags=None):
                """Save room data"""
                pass

            def get_user_activity_stats(self, username):
                """Get user activity stats"""
                return {"daily_activity": []}

            def get_global_analytics(self, days=30):
                """Get global analytics"""
                return {
                    "total_messages": 0,
                    "total_users": 0,
                    "total_rooms": 0,
                    "daily_activity": [],
                    "top_rooms": [],
                    "top_users": []
                }

        db = SimpleFileDatabase()

    USING_MONGODB = False

# Import AI modules if available
try:
    from sentiment_analyzer import MessageSentimentAnalyzer
    from recommendation_system import RoomRecommender
    from chatbot_assistant import ChatbotAssistant
    from predictive_text import PredictiveText

    # Initialize AI components with database instance
    sentiment_analyzer = MessageSentimentAnalyzer()
    room_recommender = RoomRecommender(database=db)
    chatbot = ChatbotAssistant(name="AIBot", db=db if USING_MONGODB else None)
    predictive_text = PredictiveText()

    AI_ENABLED = True
    print("AI features enabled! 🤖")
except ImportError as e:
    print(f"Some AI features may not be available: {e}")
    AI_ENABLED = False

# Ensure required directories exist for static files and backups
os.makedirs('static/images', exist_ok=True)
os.makedirs('backups', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Background task for periodic operations
def background_tasks():
    """Run periodic tasks in the background"""
    while True:
        try:
            # Create backup every 30 minutes if using MongoDB
            if USING_MONGODB and hasattr(db, 'create_backup'):
                db.create_backup()

            # Update room recommendations if AI is enabled
            if AI_ENABLED and 'room_recommender' in globals():
                room_recommender.update_room_content(force_refresh=True)

            # Sleep for 30 minutes
            time.sleep(1800)
        except Exception as e:
            print(f"Error in background task: {e}")
            time.sleep(60)  # Sleep for a minute if there's an error

# Start background thread
background_thread = threading.Thread(target=background_tasks, daemon=True)
background_thread.start()

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', ai_enabled=AI_ENABLED)

@app.route('/test')
def test():
    """Test page to verify Flask is working"""
    return render_template('test.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate input
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long', 'danger')
            return render_template('register.html')

        if not email:
            flash('Email is required', 'danger')
            return render_template('register.html')

        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')

        # Register user
        if USING_MONGODB:
            success, message = db.register_user(username, email, password)
            if not success:
                flash(message, 'danger')
                return render_template('register.html')

            # Create session
            session_id = db.create_session(username)
            session['session_id'] = session_id
            session['username'] = username

            flash('Registration successful! Welcome to AI-Enhanced Chat.', 'success')
            return redirect(url_for('rooms'))
        else:
            # Fallback for file-based storage
            session['username'] = username
            flash('Registration successful! Welcome to AI-Enhanced Chat.', 'success')
            return redirect(url_for('rooms'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'

        if not username_or_email or not password:
            flash('Please enter both username/email and password', 'danger')
            return render_template('login.html')

        if USING_MONGODB:
            # Authenticate user
            success, result = db.authenticate_user(username_or_email, password)

            if not success:
                flash(result, 'danger')
                return render_template('login.html')

            # Create session
            session_id = db.create_session(result['_id'])
            session['session_id'] = session_id
            session['username'] = result['_id']

            flash('Login successful!', 'success')
            return redirect(url_for('rooms'))
        else:
            # Fallback for file-based storage
            session['username'] = username_or_email
            flash('Login successful!', 'success')
            return redirect(url_for('rooms'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    if USING_MONGODB and 'session_id' in session:
        db.invalidate_session(session['session_id'])

    session.pop('username', None)
    session.pop('session_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('Please enter your email address', 'danger')
            return render_template('forgot_password.html')

        if USING_MONGODB:
            success, token = db.request_password_reset(email)

            if success:
                # In a real application, you would send an email with the reset link
                # For this demo, we'll just show the token
                reset_url = url_for('reset_password', token=token, _external=True)
                flash(f'Password reset link has been sent to your email. For demo purposes, here is the link: {reset_url}', 'success')
                return redirect(url_for('login'))
            else:
                flash(token, 'danger')  # token contains error message
                return render_template('forgot_password.html')
        else:
            # Fallback for file-based storage
            flash('Password reset is not available in file-based storage mode', 'warning')
            return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page"""
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html', token=token)

        if USING_MONGODB:
            success, message = db.reset_password(token, password)

            if success:
                flash('Password has been reset successfully. You can now login with your new password.', 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
                return render_template('reset_password.html', token=token)
        else:
            # Fallback for file-based storage
            flash('Password reset is not available in file-based storage mode', 'warning')
            return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

@app.route('/profile')
def profile():
    """User profile page"""
    if 'username' not in session:
        flash('Please login to view your profile', 'warning')
        return redirect(url_for('login'))

    username = session['username']

    # Get user data
    user_data = db.load_user_data(username)

    # Make sure username is in the user data
    if '_id' in user_data and 'username' not in user_data:
        user_data['username'] = user_data['_id']
    elif 'username' not in user_data:
        user_data['username'] = username

    # Get activity data for charts
    if USING_MONGODB:
        try:
            activity_data = db.get_user_activity_stats(username)

            # Format data for charts
            chart_data = {
                'dates': [],
                'message_counts': []
            }

            for day in activity_data.get('daily_activity', []):
                chart_data['dates'].append(day.get('date'))
                chart_data['message_counts'].append(day.get('message_count'))
        except Exception as e:
            print(f"Error getting activity stats: {e}")
            chart_data = {
                'dates': [],
                'message_counts': []
            }
    else:
        # Fallback for file-based storage
        chart_data = {
            'dates': [],
            'message_counts': []
        }

    # Ensure all required fields exist
    if 'email' not in user_data:
        user_data['email'] = ''
    if 'created_at' not in user_data:
        user_data['created_at'] = ''
    if 'sentiment_stats' not in user_data:
        user_data['sentiment_stats'] = {'positive': 0, 'neutral': 0, 'negative': 0}
    if 'preferences' not in user_data:
        user_data['preferences'] = {'theme': 'default', 'notifications': True, 'language': 'en'}
    if 'interests' not in user_data:
        user_data['interests'] = []
    if 'joined_rooms' not in user_data:
        user_data['joined_rooms'] = []
    if 'messages_sent' not in user_data:
        user_data['messages_sent'] = 0

    return render_template('profile.html', user=user_data, activity_data=chart_data)

@app.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    if 'username' not in session:
        flash('Please login to change your password', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    if not current_password or not new_password or not confirm_new_password:
        flash('All fields are required', 'danger')
        return redirect(url_for('profile'))

    if new_password != confirm_new_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('profile'))

    if len(new_password) < 8:
        flash('New password must be at least 8 characters long', 'danger')
        return redirect(url_for('profile'))

    if USING_MONGODB:
        success, message = db.update_password(username, current_password, new_password)

        if success:
            flash('Password updated successfully', 'success')
        else:
            flash(message, 'danger')
    else:
        # Fallback for file-based storage
        flash('Password change is not available in file-based storage mode', 'warning')

    return redirect(url_for('profile'))

@app.route('/update-profile', methods=['POST'])
def update_profile():
    """Update user profile"""
    if 'username' not in session:
        flash('Please login to update your profile', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    email = request.form.get('email')

    if not email:
        flash('Email is required', 'danger')
        return redirect(url_for('profile'))

    # Update user data
    user_data = db.load_user_data(username)
    user_data['email'] = email
    db.save_user_data(username, user_data)

    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/update-preferences', methods=['POST'])
def update_preferences():
    """Update user preferences"""
    if 'username' not in session:
        flash('Please login to update your preferences', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    theme = request.form.get('theme')
    notifications = request.form.get('notifications') == 'on'
    language = request.form.get('language')

    # Update user data
    user_data = db.load_user_data(username)

    if 'preferences' not in user_data:
        user_data['preferences'] = {}

    user_data['preferences']['theme'] = theme
    user_data['preferences']['notifications'] = notifications
    user_data['preferences']['language'] = language

    db.save_user_data(username, user_data)

    flash('Preferences updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/update-interests', methods=['POST'])
def update_interests():
    """Update user interests"""
    if 'username' not in session:
        flash('Please login to update your interests', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    interests_str = request.form.get('interests', '')

    # Parse interests
    interests = [interest.strip() for interest in interests_str.split(',') if interest.strip()]

    # Update user data
    user_data = db.load_user_data(username)
    user_data['interests'] = interests
    db.save_user_data(username, user_data)

    flash('Interests updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    if 'username' not in session:
        flash('Please login to view analytics', 'warning')
        return redirect(url_for('login'))

    # Get time range from query parameters
    days = request.args.get('days', 30, type=int)

    if USING_MONGODB:
        try:
            # Get global analytics
            analytics_data = db.get_global_analytics(days)
        except Exception as e:
            print(f"Error getting analytics: {e}")
            analytics_data = {
                'total_messages': 0,
                'total_users': 0,
                'total_rooms': 0,
                'daily_activity': [],
                'top_rooms': [],
                'top_users': []
            }
    else:
        # Fallback for file-based storage
        analytics_data = {
            'total_messages': 0,
            'total_users': 0,
            'total_rooms': 0,
            'daily_activity': [],
            'top_rooms': [],
            'top_users': []
        }

    # Ensure all required fields exist
    if 'daily_activity' not in analytics_data:
        analytics_data['daily_activity'] = []
    if 'top_rooms' not in analytics_data:
        analytics_data['top_rooms'] = []
    if 'top_users' not in analytics_data:
        analytics_data['top_users'] = []

    return render_template('analytics.html', analytics=analytics_data, time_range=days)

@app.route('/rooms')
def rooms():
    """List all available rooms"""
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get active rooms from database
    active_rooms = db.get_active_rooms(limit=50)

    # Get recommendations if AI is enabled
    recommendations = []
    if AI_ENABLED and 'username' in session:
        recommendations = room_recommender.get_user_recommendations(session['username'], top_n=3)

    return render_template('rooms.html',
                          rooms=active_rooms,
                          recommendations=recommendations,
                          username=session.get('username', ''))

@app.route('/create_room', methods=['GET', 'POST'])
def create_room():
    """Create a new chat room"""
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        room_name = request.form.get('room_name')
        room_pwd = request.form.get('room_password')
        description = request.form.get('description', '')
        tags_input = request.form.get('tags', '')
        tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []

        # Validate input
        if not room_name or len(room_name) <= 2:
            flash('Room name must be more than 2 characters', 'error')
            return render_template('create_room.html')

        # Check if room already exists
        room_details = db.load_room_data()
        if room_name in room_details:
            flash('Room already exists. Please choose another name.', 'error')
            return render_template('create_room.html')

        # Save room with enhanced metadata
        db.save_room_data(room_name, room_pwd, description, tags)

        # Create initial room message
        db.add_message_to_room(
            room_name,
            "System",
            f"Room '{room_name}' was created with description: {description}"
        )

        flash(f"Room '{room_name}' created successfully!", 'success')

        # Redirect to the new room
        return redirect(url_for('chat_room', room_name=room_name))

    return render_template('create_room.html')

@app.route('/join_room', methods=['GET', 'POST'])
def join_room():
    """Join an existing room"""
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        room_name = request.form.get('room_name')
        room_pwd = request.form.get('room_password')

        # Load room details
        room_details = db.load_room_data()

        # Clean up passwords (remove newlines)
        clean_details = {}
        for room, pwd in room_details.items():
            if '\n' in pwd:
                clean_details[room] = pwd.strip()
            else:
                clean_details[room] = pwd

        # Check if room exists and password matches
        if room_name in clean_details and clean_details[room_name] == room_pwd:
            # Update user activity
            if AI_ENABLED:
                db.update_user_activity(session['username'], room_name, "join")

            # Redirect to chat room
            return redirect(url_for('chat_room', room_name=room_name))
        else:
            flash('Incorrect room name or password', 'error')
            return redirect(url_for('rooms'))

    # If GET request, show room selection
    room_name = request.args.get('room_name', '')
    return render_template('join_room.html', room_name=room_name)

@app.route('/chat/<room_name>')
def chat_room(room_name):
    """Chat room page"""
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get room metadata
    room_metadata = db.get_room_metadata(room_name)

    # Update user activity
    if AI_ENABLED:
        db.update_user_activity(session['username'], room_name, "join")

    return render_template('chat_room.html',
                          room_name=room_name,
                          room_metadata=room_metadata,
                          username=session.get('username', ''),
                          ai_enabled=AI_ENABLED,
                          websocket_enabled=WEBSOCKET_ENABLED)

@app.route('/api/messages/<room_name>', methods=['GET'])
def get_messages(room_name):
    """API endpoint to get messages from a room"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    # Get messages from database
    messages = db.get_room_messages(room_name, limit=50)

    return jsonify({'messages': messages})

@app.route('/api/messages/<room_name>', methods=['POST'])
def send_message(room_name):
    """API endpoint to send a message to a room"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.json
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Empty message'}), 400

    # Process message with AI components
    sentiment_score = None
    if AI_ENABLED:
        # Analyze sentiment
        sentiment = sentiment_analyzer.analyze_message(message)
        sentiment_score = sentiment.get('compound', 0)

        # Update user models
        predictive_text.train_on_message(session['username'], message)
        room_recommender.update_user_interest(session['username'], message)

    # Save message using database
    success = db.add_message_to_room(room_name, session['username'], message, sentiment_score)

    if success:
        # Broadcast message via WebSockets if enabled
        if WEBSOCKET_ENABLED:
            broadcast_to_room(room_name, 'chat_message', {
                'username': session['username'],
                'room': room_name,
                'message': message,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'sentiment': sentiment_score
            })

        # Check if message is directed to the chatbot
        if AI_ENABLED and (message.lower().startswith('@aibot') or message.lower().startswith('@ai')):
            bot_query = message.split(' ', 1)[1] if ' ' in message else ""
            bot_response = chatbot.get_response(bot_query, room_name, session['username'])

            # Add bot response to chat
            time.sleep(1)  # Simulate thinking
            db.add_message_to_room(room_name, "AIBot", bot_response)

            # Broadcast bot response via WebSockets if enabled
            if WEBSOCKET_ENABLED:
                broadcast_to_room(room_name, 'chat_message', {
                    'username': "AIBot",
                    'room': room_name,
                    'message': bot_response,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'sentiment': None
                })

        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'Failed to send message'}), 500

@app.route('/api/sentiment/<room_name>')
def get_sentiment(room_name):
    """API endpoint to get sentiment analysis for a room"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    if not AI_ENABLED:
        return jsonify({'error': 'AI features not enabled'}), 400

    # Get messages from database
    messages = db.get_room_messages(room_name, limit=100)

    if not messages:
        return jsonify({'error': 'Not enough messages for analysis'}), 400

    # Extract message content
    message_texts = [msg["content"] for msg in messages]

    # Analyze sentiment
    sentiment_scores = sentiment_analyzer.analyze_conversation(message_texts)

    # Calculate average
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

    # Count sentiment categories
    categories = {
        "Very Positive": 0,
        "Positive": 0,
        "Neutral": 0,
        "Negative": 0,
        "Very Negative": 0
    }

    for score in sentiment_scores:
        label = get_sentiment_label(score)
        categories[label] += 1

    # Find most positive and negative messages
    most_positive_idx = sentiment_scores.index(max(sentiment_scores))
    most_negative_idx = sentiment_scores.index(min(sentiment_scores))

    result = {
        'average_sentiment': avg_sentiment,
        'sentiment_label': get_sentiment_label(avg_sentiment),
        'message_count': len(message_texts),
        'categories': categories,
        'most_positive': {
            'message': message_texts[most_positive_idx],
            'score': sentiment_scores[most_positive_idx],
            'author': messages[most_positive_idx]['username']
        },
        'most_negative': {
            'message': message_texts[most_negative_idx],
            'score': sentiment_scores[most_negative_idx],
            'author': messages[most_negative_idx]['username']
        }
    }

    return jsonify(result)

@app.route('/api/recommendations/<username>')
def get_recommendations(username):
    """API endpoint to get room recommendations"""
    if 'username' not in session or session['username'] != username:
        return jsonify({'error': 'Not authorized'}), 401

    if not AI_ENABLED:
        return jsonify({'error': 'AI features not enabled'}), 400

    # Get algorithm if specified
    algorithm = request.args.get('algorithm', 'hybrid')
    if algorithm not in ['content', 'collaborative', 'topic', 'hybrid']:
        algorithm = 'hybrid'

    # Get recommendations
    recommendations = room_recommender.get_user_recommendations(username, algorithm=algorithm)

    # Get metadata for each recommended room
    result = []
    for room_name in recommendations:
        metadata = db.get_room_metadata(room_name)
        result.append({
            'name': room_name,
            'description': metadata.get('description', ''),
            'message_count': metadata.get('message_count', 0),
            'tags': metadata.get('tags', []),
            'explanation': room_recommender.get_recommendation_explanation(username, room_name)
        })

    return jsonify(result)

@app.route('/api/trending')
def get_trending():
    """API endpoint to get trending topics"""
    if not AI_ENABLED:
        return jsonify({'error': 'AI features not enabled'}), 400

    # Get trending topics
    topics = room_recommender.get_trending_topics(num_topics=5, num_words=5)

    return jsonify({'topics': topics})

@app.route('/api/user/<username>')
def get_user_stats(username):
    """API endpoint to get user statistics"""
    if 'username' not in session or session['username'] != username:
        return jsonify({'error': 'Not authorized'}), 401

    # Get user data
    user_data = db.load_user_data(username)

    # Get room metadata for joined rooms
    joined_rooms = []
    for room_name in user_data.get('joined_rooms', []):
        metadata = db.get_room_metadata(room_name)
        joined_rooms.append({
            'name': room_name,
            'description': metadata.get('description', ''),
            'message_count': metadata.get('message_count', 0),
            'tags': metadata.get('tags', [])
        })

    # Prepare result
    result = {
        'username': username,
        'messages_sent': user_data.get('messages_sent', 0),
        'joined_rooms': joined_rooms,
        'interests': user_data.get('interests', []),
        'sentiment_stats': user_data.get('sentiment_stats', {})
    }

    return jsonify(result)

@app.route('/api/predict')
def get_predictions():
    """API endpoint to get word predictions"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    if not AI_ENABLED:
        return jsonify({'error': 'AI features not enabled'}), 400

    # Get current text
    current_text = request.args.get('text', '')

    # Get predictions
    predictions = predictive_text.predict_next_word(session['username'], current_text, 5)

    return jsonify({'predictions': predictions})

def get_sentiment_label(score):
    """Convert sentiment score to human-readable label"""
    if score >= 0.5:
        return "Very Positive"
    elif score > 0:
        return "Positive"
    elif score == 0:
        return "Neutral"
    elif score > -0.5:
        return "Negative"
    else:
        return "Very Negative"

if __name__ == '__main__':
    # Get host and port from environment variables
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))

    # Run with WebSockets if available, otherwise use standard Flask
    if WEBSOCKET_ENABLED:
        socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True)
    else:
        app.run(host=host, port=port, debug=True)
