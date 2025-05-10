import pymongo
from datetime import datetime, timedelta
import hashlib
import os
import re
import uuid
import bcrypt
from collections import Counter
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError

# Import Redis cache (with fallback if Redis is not available)
try:
    from redis_cache import RedisCache
    cache = RedisCache()
except ImportError:
    print("Redis cache not available, running without caching")
    cache = None

# Load environment variables
load_dotenv()

class MongoDBConnector:
    def __init__(self):
        # Get MongoDB connection string from environment variable
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("DB_NAME", "ai_chat_app")

        # Connect to MongoDB
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[db_name]

        # Create collections
        self.users = self.db.users
        self.rooms = self.db.rooms
        self.messages = self.db.messages
        self.ai_data = self.db.ai_data
        self.sessions = self.db.sessions

        # Create indexes for better performance
        self.messages.create_index([("room_id", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING)])

        # Create email index with partial filter to exclude null values
        self.users.create_index(
            [("email", pymongo.ASCENDING)],
            unique=True,
            partialFilterExpression={"email": {"$type": "string"}}
        )

        self.sessions.create_index("expires", expireAfterSeconds=0)  # TTL index for auto-expiry

    # User Authentication Methods
    def register_user(self, username, email, password):
        """Register a new user with email and password"""
        try:
            # Validate email
            valid_email = validate_email(email)
            email = valid_email.normalized

            # Check if username exists
            if self.users.find_one({"_id": username}):
                return False, "Username already exists"

            # Check if email exists
            if self.users.find_one({"email": email}):
                return False, "Email already registered"

            # Validate password strength
            if len(password) < 8:
                return False, "Password must be at least 8 characters long"

            # Hash password
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

            # Create user document
            user_data = {
                "_id": username,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.now().isoformat(),
                "joined_rooms": [],
                "messages_sent": 0,
                "last_active": None,
                "interests": [],
                "message_history": [],
                "sentiment_stats": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "preferences": {
                    "theme": "default",
                    "notifications": True,
                    "language": "en"
                },
                "role": "user"  # Default role
            }

            # Insert user
            self.users.insert_one(user_data)
            return True, "User registered successfully"

        except EmailNotValidError as e:
            return False, f"Invalid email: {str(e)}"
        except Exception as e:
            return False, f"Registration error: {str(e)}"

    def authenticate_user(self, username_or_email, password):
        """Authenticate a user with username/email and password"""
        try:
            # Find user by username or email
            user = self.users.find_one({"$or": [{"_id": username_or_email}, {"email": username_or_email}]})

            if not user:
                return False, "User not found"

            # Check password
            if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
                return True, user
            else:
                return False, "Incorrect password"

        except Exception as e:
            return False, f"Authentication error: {str(e)}"

    def create_session(self, user_id):
        """Create a new session for a user"""
        session_id = str(uuid.uuid4())
        expires = datetime.now() + timedelta(days=7)  # Session expires in 7 days

        session_data = {
            "_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "expires": expires,
            "user_agent": None,
            "ip_address": None
        }

        self.sessions.insert_one(session_data)
        return session_id

    def validate_session(self, session_id):
        """Validate a session and return the user"""
        if not session_id:
            return None

        session = self.sessions.find_one({"_id": session_id})
        if not session:
            return None

        # Get user data
        user = self.users.find_one({"_id": session["user_id"]})
        return user

    def invalidate_session(self, session_id):
        """Invalidate a session"""
        if session_id:
            self.sessions.delete_one({"_id": session_id})
        return True

    def update_password(self, user_id, current_password, new_password):
        """Update a user's password"""
        # Find user
        user = self.users.find_one({"_id": user_id})
        if not user:
            return False, "User not found"

        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), user["password"]):
            return False, "Current password is incorrect"

        # Validate new password
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters long"

        # Hash new password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)

        # Update password
        self.users.update_one(
            {"_id": user_id},
            {"$set": {"password": hashed_password}}
        )

        return True, "Password updated successfully"

    def request_password_reset(self, email):
        """Generate a password reset token"""
        user = self.users.find_one({"email": email})
        if not user:
            return False, "Email not found"

        # Generate reset token
        reset_token = str(uuid.uuid4())
        expires = datetime.now() + timedelta(hours=24)  # Token expires in 24 hours

        # Store reset token
        self.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "reset_token": reset_token,
                "reset_token_expires": expires
            }}
        )

        return True, reset_token

    def reset_password(self, token, new_password):
        """Reset password using a token"""
        # Find user with this token
        user = self.users.find_one({
            "reset_token": token,
            "reset_token_expires": {"$gt": datetime.now()}
        })

        if not user:
            return False, "Invalid or expired token"

        # Validate new password
        if len(new_password) < 8:
            return False, "Password must be at least 8 characters long"

        # Hash new password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)

        # Update password and remove token
        self.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"password": hashed_password},
                "$unset": {"reset_token": "", "reset_token_expires": ""}
            }
        )

        return True, "Password reset successfully"

    # User Data Methods
    def load_user_data(self, username):
        """Load user data from database with caching"""
        # Try to get from cache first
        if cache and cache.enabled:
            cached_data = cache.get_user_data(username)
            if cached_data:
                return cached_data

        # Get from database
        user = self.users.find_one({"_id": username})

        if not user:
            # Return default user data if not found
            default_data = {
                "username": username,
                "joined_rooms": [],
                "messages_sent": 0,
                "last_active": None,
                "interests": [],
                "message_history": [],
                "sentiment_stats": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "preferences": {
                    "theme": "default",
                    "notifications": True,
                    "language": "en"
                }
            }
            return default_data

        # Cache the result
        if cache and cache.enabled:
            cache.cache_user_data(username, user)

        return user

    def save_user_data(self, username, data):
        """Save user data to database"""
        # Don't overwrite critical fields
        if "_id" in data and data["_id"] != username:
            data["_id"] = username

        # Don't allow changing email or password through this method
        if "email" in data:
            del data["email"]
        if "password" in data:
            del data["password"]

        # Update in database
        self.users.update_one(
            {"_id": username},
            {"$set": data},
            upsert=True
        )

        # Invalidate cache
        if cache and cache.enabled:
            cache.invalidate_user_data(username)

    def update_user_activity(self, username, room_name, action, message=None, sentiment=None):
        """Update user activity data with enhanced tracking"""
        user_data = self.load_user_data(username)

        # Update basic stats
        timestamp = datetime.now().isoformat()
        user_data["last_active"] = timestamp

        # Track action
        if "activity_log" not in user_data:
            user_data["activity_log"] = []

        activity = {
            "timestamp": timestamp,
            "action": action,
            "room": room_name
        }

        # Add message data if provided
        if action == "message" and message:
            user_data["messages_sent"] = user_data.get("messages_sent", 0) + 1

            # Store message in history (limited to last 50)
            if "message_history" not in user_data:
                user_data["message_history"] = []

            message_data = {
                "timestamp": timestamp,
                "room": room_name,
                "content": message,
                "sentiment": sentiment
            }

            user_data["message_history"].insert(0, message_data)
            user_data["message_history"] = user_data["message_history"][:50]  # Keep only last 50

            # Extract potential interests from message
            self._update_user_interests(user_data, message)

            # Update sentiment stats if provided
            if sentiment:
                if "sentiment_stats" not in user_data:
                    user_data["sentiment_stats"] = {"positive": 0, "neutral": 0, "negative": 0}

                if sentiment > 0.1:
                    user_data["sentiment_stats"]["positive"] += 1
                elif sentiment < -0.1:
                    user_data["sentiment_stats"]["negative"] += 1
                else:
                    user_data["sentiment_stats"]["neutral"] += 1

            # Update room message count
            self._update_room_message_count(room_name, username)

        # Update joined rooms
        if room_name and room_name not in user_data.get("joined_rooms", []):
            if "joined_rooms" not in user_data:
                user_data["joined_rooms"] = []
            user_data["joined_rooms"].append(room_name)

        # Add activity to log
        user_data["activity_log"].insert(0, activity)
        user_data["activity_log"] = user_data["activity_log"][:100]  # Keep only last 100

        # Save updated data
        self.save_user_data(username, user_data)

        return True

    def get_user_interests(self, username):
        """Get user interests based on message history"""
        user_data = self.load_user_data(username)
        return user_data.get("interests", [])

    # Advanced Analytics Methods using MongoDB Aggregation
    def get_user_activity_stats(self, username, days=30):
        """Get detailed user activity statistics using aggregation"""
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Convert to ISO format for string comparison
        start_date_str = start_date.isoformat()

        # Aggregation pipeline for message activity by day
        pipeline = [
            # Match messages from this user in the date range
            {"$match": {
                "username": username,
                "timestamp": {"$gte": start_date_str}
            }},
            # Extract date part from timestamp
            {"$addFields": {
                "date": {"$substr": ["$timestamp", 0, 10]}
            }},
            # Group by date
            {"$group": {
                "_id": "$date",
                "message_count": {"$sum": 1},
                "rooms": {"$addToSet": "$room_id"},
                "avg_sentiment": {"$avg": "$sentiment"}
            }},
            # Sort by date
            {"$sort": {"_id": 1}},
            # Add metadata
            {"$addFields": {
                "date": "$_id",
                "unique_rooms": {"$size": "$rooms"}
            }},
            # Project final fields
            {"$project": {
                "_id": 0,
                "date": 1,
                "message_count": 1,
                "unique_rooms": 1,
                "avg_sentiment": 1
            }}
        ]

        daily_activity = list(self.messages.aggregate(pipeline))

        # Aggregation for room participation
        room_pipeline = [
            {"$match": {"username": username}},
            {"$group": {
                "_id": "$room_id",
                "message_count": {"$sum": 1},
                "first_message": {"$min": "$timestamp"},
                "last_message": {"$max": "$timestamp"}
            }},
            {"$sort": {"message_count": -1}},
            {"$limit": 10}  # Top 10 rooms
        ]

        room_activity = list(self.messages.aggregate(room_pipeline))

        # Get room metadata for each room
        for room in room_activity:
            metadata = self.get_room_metadata(room["_id"])
            room["name"] = metadata.get("name", room["_id"])
            room["description"] = metadata.get("description", "")
            room["tags"] = metadata.get("tags", [])

        # Sentiment distribution
        sentiment_pipeline = [
            {"$match": {
                "username": username,
                "sentiment": {"$ne": None}
            }},
            {"$group": {
                "_id": {
                    "$switch": {
                        "branches": [
                            {"case": {"$gte": ["$sentiment", 0.5]}, "then": "Very Positive"},
                            {"case": {"$gt": ["$sentiment", 0]}, "then": "Positive"},
                            {"case": {"$eq": ["$sentiment", 0]}, "then": "Neutral"},
                            {"case": {"$gt": ["$sentiment", -0.5]}, "then": "Negative"}
                        ],
                        "default": "Very Negative"
                    }
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]

        sentiment_distribution = list(self.messages.aggregate(sentiment_pipeline))

        # Overall statistics
        total_messages = self.messages.count_documents({"username": username})
        total_rooms = len(set(msg["room_id"] for msg in self.messages.find({"username": username}, {"room_id": 1})))

        # Compile results
        return {
            "username": username,
            "total_messages": total_messages,
            "total_rooms": total_rooms,
            "daily_activity": daily_activity,
            "room_activity": room_activity,
            "sentiment_distribution": sentiment_distribution
        }

    def update_user_interests(self, username, interests):
        """Manually update user interests"""
        user_data = self.load_user_data(username)

        if "interests" not in user_data:
            user_data["interests"] = []

        # Add new interests
        for interest in interests:
            if interest not in user_data["interests"]:
                user_data["interests"].append(interest)

        # Save updated data
        self.save_user_data(username, user_data)

        return True

    # Room methods
    def load_room_data(self):
        """Load all rooms with their passwords"""
        room_details = {}
        rooms = self.rooms.find({}, {"_id": 1, "password": 1})

        for room in rooms:
            room_details[room["_id"]] = room["password"]

        return room_details

    def save_room_data(self, room_name, room_pwd, description="", tags=None):
        """Save room data to database"""
        if tags is None:
            tags = []

        # Create room document
        room_data = {
            "_id": room_name,
            "password": room_pwd,
            "created_at": datetime.now().isoformat(),
            "description": description,
            "tags": tags,
            "message_count": 0,
            "active_users": [],
            "last_activity": datetime.now().isoformat()
        }

        # Insert or update room
        self.rooms.replace_one({"_id": room_name}, room_data, upsert=True)

        return True

    def get_room_metadata(self, room_name):
        """Get metadata for a specific room with caching"""
        # Try to get from cache first
        if cache and cache.enabled:
            cached_data = cache.get_room_metadata(room_name)
            if cached_data:
                return cached_data

        # Get from database
        room = self.rooms.find_one({"_id": room_name})

        if not room:
            # Return default metadata
            default_data = {
                "name": room_name,
                "created_at": datetime.now().isoformat(),
                "description": "",
                "tags": [],
                "message_count": 0,
                "active_users": [],
                "last_activity": datetime.now().isoformat()
            }
            return default_data

        # Add name field for compatibility with existing code
        room["name"] = room["_id"]

        # Cache the result
        if cache and cache.enabled:
            cache.cache_room_metadata(room_name, room)

        return room

    def get_active_rooms(self, limit=10):
        """Get most active rooms based on recent activity with caching"""
        # Try to get from cache first
        if cache and cache.enabled:
            cached_data = cache.get_active_rooms(limit)
            if cached_data:
                return cached_data

        # Get from database
        rooms = list(self.rooms.find().sort("last_activity", pymongo.DESCENDING).limit(limit))

        # Format for compatibility with existing code
        formatted_rooms = []
        for room in rooms:
            formatted_rooms.append({
                "name": room["_id"],
                "message_count": room.get("message_count", 0),
                "last_activity": room.get("last_activity", ""),
                "description": room.get("description", ""),
                "tags": room.get("tags", []),
                "active_users": len(room.get("active_users", []))
            })

        # Cache the result
        if cache and cache.enabled:
            cache.cache_active_rooms(formatted_rooms, limit)

        return formatted_rooms

    def get_room_analytics(self, room_name, days=30):
        """Get detailed analytics for a specific room using aggregation with caching"""
        # Try to get from cache first
        if cache and cache.enabled:
            cached_data = cache.get_analytics(f"room:{room_name}", days)
            if cached_data:
                return cached_data
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Convert to ISO format for string comparison
        start_date_str = start_date.isoformat()

        # Message volume by day
        volume_pipeline = [
            {"$match": {
                "room_id": room_name,
                "timestamp": {"$gte": start_date_str}
            }},
            {"$addFields": {
                "date": {"$substr": ["$timestamp", 0, 10]}
            }},
            {"$group": {
                "_id": "$date",
                "message_count": {"$sum": 1},
                "unique_users": {"$addToSet": "$username"},
                "avg_sentiment": {"$avg": "$sentiment"}
            }},
            {"$addFields": {
                "date": "$_id",
                "user_count": {"$size": "$unique_users"}
            }},
            {"$project": {
                "_id": 0,
                "date": 1,
                "message_count": 1,
                "user_count": 1,
                "avg_sentiment": 1
            }},
            {"$sort": {"date": 1}}
        ]

        daily_activity = list(self.messages.aggregate(volume_pipeline))

        # Most active users
        user_pipeline = [
            {"$match": {"room_id": room_name}},
            {"$group": {
                "_id": "$username",
                "message_count": {"$sum": 1},
                "first_message": {"$min": "$timestamp"},
                "last_message": {"$max": "$timestamp"},
                "avg_sentiment": {"$avg": "$sentiment"}
            }},
            {"$sort": {"message_count": -1}},
            {"$limit": 10}  # Top 10 users
        ]

        top_users = list(self.messages.aggregate(user_pipeline))

        # Sentiment trends
        sentiment_pipeline = [
            {"$match": {
                "room_id": room_name,
                "sentiment": {"$ne": None},
                "timestamp": {"$gte": start_date_str}
            }},
            {"$addFields": {
                "date": {"$substr": ["$timestamp", 0, 10]},
                "sentiment_category": {
                    "$switch": {
                        "branches": [
                            {"case": {"$gte": ["$sentiment", 0.5]}, "then": "Very Positive"},
                            {"case": {"$gt": ["$sentiment", 0]}, "then": "Positive"},
                            {"case": {"$eq": ["$sentiment", 0]}, "then": "Neutral"},
                            {"case": {"$gt": ["$sentiment", -0.5]}, "then": "Negative"}
                        ],
                        "default": "Very Negative"
                    }
                }
            }},
            {"$group": {
                "_id": {
                    "date": "$date",
                    "category": "$sentiment_category"
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.date": 1, "_id.category": 1}}
        ]

        sentiment_trends = list(self.messages.aggregate(sentiment_pipeline))

        # Format sentiment trends for easier consumption
        formatted_sentiment = {}
        for item in sentiment_trends:
            date = item["_id"]["date"]
            category = item["_id"]["category"]
            count = item["count"]

            if date not in formatted_sentiment:
                formatted_sentiment[date] = {}

            formatted_sentiment[date][category] = count

        # Overall statistics
        total_messages = self.messages.count_documents({"room_id": room_name})
        unique_users = len(set(msg["username"] for msg in self.messages.find({"room_id": room_name}, {"username": 1})))

        # Get room metadata
        metadata = self.get_room_metadata(room_name)

        # Compile results
        result = {
            "room_name": room_name,
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
            "created_at": metadata.get("created_at", ""),
            "total_messages": total_messages,
            "unique_users": unique_users,
            "daily_activity": daily_activity,
            "top_users": top_users,
            "sentiment_trends": formatted_sentiment
        }

        # Cache the result
        if cache and cache.enabled:
            cache.cache_analytics(f"room:{room_name}", result, days)

        return result

    def get_global_analytics(self, days=30):
        """Get global analytics across all rooms and users with caching"""
        # Try to get from cache first
        if cache and cache.enabled:
            cached_data = cache.get_analytics("global", days)
            if cached_data:
                return cached_data
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Convert to ISO format for string comparison
        start_date_str = start_date.isoformat()

        # Overall activity by day
        activity_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date_str}}},
            {"$addFields": {
                "date": {"$substr": ["$timestamp", 0, 10]}
            }},
            {"$group": {
                "_id": "$date",
                "message_count": {"$sum": 1},
                "unique_users": {"$addToSet": "$username"},
                "unique_rooms": {"$addToSet": "$room_id"},
                "avg_sentiment": {"$avg": "$sentiment"}
            }},
            {"$addFields": {
                "date": "$_id",
                "user_count": {"$size": "$unique_users"},
                "room_count": {"$size": "$unique_rooms"}
            }},
            {"$project": {
                "_id": 0,
                "date": 1,
                "message_count": 1,
                "user_count": 1,
                "room_count": 1,
                "avg_sentiment": 1
            }},
            {"$sort": {"date": 1}}
        ]

        daily_activity = list(self.messages.aggregate(activity_pipeline))

        # Most active rooms
        room_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date_str}}},
            {"$group": {
                "_id": "$room_id",
                "message_count": {"$sum": 1},
                "unique_users": {"$addToSet": "$username"},
                "avg_sentiment": {"$avg": "$sentiment"}
            }},
            {"$addFields": {
                "user_count": {"$size": "$unique_users"}
            }},
            {"$sort": {"message_count": -1}},
            {"$limit": 10}  # Top 10 rooms
        ]

        top_rooms = list(self.messages.aggregate(room_pipeline))

        # Add room metadata
        for room in top_rooms:
            metadata = self.get_room_metadata(room["_id"])
            room["name"] = metadata.get("name", room["_id"])
            room["description"] = metadata.get("description", "")
            room["tags"] = metadata.get("tags", [])

        # Most active users
        user_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date_str}}},
            {"$group": {
                "_id": "$username",
                "message_count": {"$sum": 1},
                "unique_rooms": {"$addToSet": "$room_id"},
                "avg_sentiment": {"$avg": "$sentiment"}
            }},
            {"$addFields": {
                "room_count": {"$size": "$unique_rooms"}
            }},
            {"$sort": {"message_count": -1}},
            {"$limit": 10}  # Top 10 users
        ]

        top_users = list(self.messages.aggregate(user_pipeline))

        # Overall statistics
        total_messages = self.messages.count_documents({})
        total_users = self.users.count_documents({})
        total_rooms = self.rooms.count_documents({})

        # Compile results
        result = {
            "total_messages": total_messages,
            "total_users": total_users,
            "total_rooms": total_rooms,
            "daily_activity": daily_activity,
            "top_rooms": top_rooms,
            "top_users": top_users
        }

        # Cache the result
        if cache and cache.enabled:
            cache.cache_analytics("global", result, days)

        return result

    def search_rooms(self, query, by_tags=False):
        """Search for rooms by name, description or tags"""
        query = query.lower()
        results = []

        # Get all rooms
        rooms = self.rooms.find()

        for room in rooms:
            score = 0
            room_name = room["_id"].lower()

            # Match by name
            if query in room_name:
                score += 3

            # Match by description
            description = room.get("description", "").lower()
            if query in description:
                score += 2

            # Match by tags
            tags = room.get("tags", [])
            if by_tags:
                if query in [tag.lower() for tag in tags]:
                    score += 4
            else:
                for tag in tags:
                    if query in tag.lower():
                        score += 1

            if score > 0:
                results.append({
                    "name": room["_id"],
                    "score": score,
                    "description": room.get("description", ""),
                    "tags": room.get("tags", []),
                    "message_count": room.get("message_count", 0)
                })

        # Sort by score (highest first)
        results.sort(key=lambda x: x["score"], reverse=True)

        return results

    # Message methods
    def get_room_messages(self, room_name, limit=50):
        """Get messages from a room with caching"""
        # Try to get from cache first
        if cache and cache.enabled:
            cached_messages = cache.get_room_messages(room_name, limit)
            if cached_messages:
                return cached_messages

        # Get from database
        messages = list(self.messages.find(
            {"room_id": room_name},
            {"_id": 0, "timestamp": 1, "username": 1, "content": 1}
        ).sort("timestamp", pymongo.DESCENDING).limit(limit))

        # Reverse to get chronological order
        messages.reverse()

        # Cache the result
        if cache and cache.enabled:
            cache.cache_room_messages(room_name, messages, limit)

        return messages

    def add_message_to_room(self, room_name, username, message, sentiment=None):
        """Add a message to a room and update metadata"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create message document
            message_data = {
                "room_id": room_name,
                "username": username,
                "content": message,
                "timestamp": timestamp,
                "sentiment": sentiment
            }

            # Insert message
            self.messages.insert_one(message_data)

            # Update user activity
            self.update_user_activity(username, room_name, "message", message, sentiment)

            # Invalidate cache for this room's messages
            if cache and cache.enabled:
                cache.invalidate_room_messages(room_name)

            return True
        except Exception as e:
            print(f"Error adding message: {e}")
            return False

    # AI data methods
    def load_ai_data(self, data_type):
        """Load AI data from database"""
        data = self.ai_data.find_one({"type": data_type})

        if not data:
            return None

        return data.get("data")

    def save_ai_data(self, data_type, data):
        """Save AI data to database"""
        self.ai_data.replace_one(
            {"type": data_type},
            {"type": data_type, "data": data},
            upsert=True
        )

    # Helper methods
    def _update_user_interests(self, user_data, message):
        """Extract potential interests from user messages"""
        if "interests" not in user_data:
            user_data["interests"] = []

        # Simple keyword extraction (could be improved with NLP)
        words = re.findall(r'\b\w{4,}\b', message.lower())

        # Filter out common words
        common_words = {"this", "that", "with", "from", "have", "what", "when", "where", "there", "their", "they", "about"}
        filtered_words = [word for word in words if word not in common_words]

        # Add most frequent words as interests
        if "word_counts" not in user_data:
            user_data["word_counts"] = {}

        for word in filtered_words:
            if word in user_data["word_counts"]:
                user_data["word_counts"][word] += 1
            else:
                user_data["word_counts"][word] = 1

            # If word appears frequently, add as interest
            if user_data["word_counts"][word] >= 3 and word not in user_data["interests"]:
                user_data["interests"].append(word)

        # Limit interests to top 20
        if len(user_data["interests"]) > 20:
            # Sort by frequency
            sorted_interests = sorted(
                user_data["interests"],
                key=lambda x: user_data["word_counts"].get(x, 0),
                reverse=True
            )
            user_data["interests"] = sorted_interests[:20]

    def _update_room_message_count(self, room_name, username):
        """Update message count and active users for a room"""
        # Update room document
        self.rooms.update_one(
            {"_id": room_name},
            {
                "$inc": {"message_count": 1},
                "$set": {"last_activity": datetime.now().isoformat()},
                "$addToSet": {"active_users": username}
            }
        )

    # Migration methods
    def migrate_from_files(self):
        """Migrate data from files to MongoDB"""
        import os
        import json

        print("Starting migration from files to MongoDB...")

        # Migrate rooms
        if os.path.exists('Database.txt'):
            print("Migrating rooms from Database.txt...")
            with open('Database.txt', 'r') as f:
                lines = f.readlines()

            for line in lines:
                if ':' in line:
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        room_name = parts[0]
                        room_pwd = parts[1]

                        # Check if room metadata exists
                        metadata_file = os.path.join('room_metadata', f"{room_name}.json")
                        if os.path.exists(metadata_file):
                            with open(metadata_file, 'r') as f:
                                try:
                                    metadata = json.load(f)
                                    self.save_room_data(
                                        room_name,
                                        room_pwd,
                                        metadata.get("description", ""),
                                        metadata.get("tags", [])
                                    )

                                    # Update other fields
                                    self.rooms.update_one(
                                        {"_id": room_name},
                                        {
                                            "$set": {
                                                "message_count": metadata.get("message_count", 0),
                                                "active_users": metadata.get("active_users", []),
                                                "created_at": metadata.get("created_at", datetime.now().isoformat()),
                                                "last_activity": metadata.get("last_activity", datetime.now().isoformat())
                                            }
                                        }
                                    )
                                    print(f"Migrated room with metadata: {room_name}")
                                except Exception as e:
                                    print(f"Error migrating room metadata for {room_name}: {e}")
                                    # Just save basic room data
                                    self.save_room_data(room_name, room_pwd)
                        else:
                            # Just save basic room data
                            self.save_room_data(room_name, room_pwd)
                            print(f"Migrated basic room: {room_name}")

        # Migrate messages
        if os.path.exists('rooms'):
            print("Migrating messages from room files...")
            for filename in os.listdir('rooms'):
                if filename.endswith('.txt'):
                    room_name = filename[:-4]  # Remove .txt extension
                    print(f"Processing messages for room: {room_name}")

                    with open(os.path.join('rooms', filename), 'r') as f:
                        lines = f.readlines()

                    message_count = 0
                    for line in lines:
                        line = line.strip()
                        if ': ' in line and '[' in line and ']' in line:
                            try:
                                # Extract timestamp, username and content
                                timestamp_part = line[line.find('[')+1:line.find(']')]
                                rest = line[line.find(']')+1:].strip()
                                username, content = rest.split(':', 1)

                                # Create message document
                                message_data = {
                                    "room_id": room_name,
                                    "username": username.strip(),
                                    "content": content.strip(),
                                    "timestamp": timestamp_part,
                                    "sentiment": None  # We don't have sentiment data for old messages
                                }

                                # Insert message
                                self.messages.insert_one(message_data)
                                message_count += 1
                            except Exception as e:
                                print(f"Error migrating message: {line} - {e}")

                    print(f"Migrated {message_count} messages for room: {room_name}")

        # Migrate user data
        if os.path.exists('user_data'):
            print("Migrating user data...")
            for filename in os.listdir('user_data'):
                if filename.endswith('.json'):
                    username = filename[:-5]  # Remove .json extension

                    with open(os.path.join('user_data', filename), 'r') as f:
                        try:
                            user_data = json.load(f)
                            user_data["_id"] = username  # Ensure _id is set

                            # Insert or update user
                            self.users.replace_one({"_id": username}, user_data, upsert=True)
                            print(f"Migrated user: {username}")
                        except Exception as e:
                            print(f"Error migrating user {username}: {e}")

        # Migrate AI data (chatbot knowledge base)
        if os.path.exists('chatbot_data'):
            print("Migrating AI data...")
            for filename in os.listdir('chatbot_data'):
                if filename.endswith('.json'):
                    data_type = filename[:-5]  # Remove .json extension

                    with open(os.path.join('chatbot_data', filename), 'r') as f:
                        try:
                            data = json.load(f)

                            # Insert or update AI data
                            self.ai_data.replace_one(
                                {"type": data_type},
                                {"type": data_type, "data": data},
                                upsert=True
                            )
                            print(f"Migrated AI data: {data_type}")
                        except Exception as e:
                            print(f"Error migrating AI data {data_type}: {e}")

        print("Migration completed!")

    def create_backup(self):
        """Create a backup of the database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join('backups', f"mongo_backup_{timestamp}")

        try:
            # Create backup directory
            os.makedirs(backup_dir, exist_ok=True)

            # Backup users
            users = list(self.users.find())
            with open(os.path.join(backup_dir, 'users.json'), 'w') as f:
                import json
                json.dump(users, f, default=str, indent=2)

            # Backup rooms
            rooms = list(self.rooms.find())
            with open(os.path.join(backup_dir, 'rooms.json'), 'w') as f:
                import json
                json.dump(rooms, f, default=str, indent=2)

            # Backup messages (this could be large)
            messages = list(self.messages.find())
            with open(os.path.join(backup_dir, 'messages.json'), 'w') as f:
                import json
                json.dump(messages, f, default=str, indent=2)

            # Backup AI data
            ai_data = list(self.ai_data.find())
            with open(os.path.join(backup_dir, 'ai_data.json'), 'w') as f:
                import json
                json.dump(ai_data, f, default=str, indent=2)

            return backup_dir
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
