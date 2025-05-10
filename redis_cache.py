import redis
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RedisCache:
    """Redis caching layer for improved performance"""
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            # Get Redis connection string from environment variable
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            
            # Connect to Redis
            self.redis = redis.from_url(redis_url)
            self.enabled = True
            print("Redis caching enabled")
            
            # Test connection
            self.redis.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            print("Running without Redis caching")
            self.enabled = False
    
    def get(self, key):
        """Get value from cache"""
        if not self.enabled:
            return None
            
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key, value, expire=3600):
        """Set value in cache with expiration time in seconds (default: 1 hour)"""
        if not self.enabled:
            return False
            
        try:
            self.redis.setex(key, expire, json.dumps(value))
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key):
        """Delete value from cache"""
        if not self.enabled:
            return False
            
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def clear_all(self):
        """Clear all cache (use with caution)"""
        if not self.enabled:
            return False
            
        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            print(f"Redis clear error: {e}")
            return False
    
    def get_room_messages(self, room_name, limit=50):
        """Get cached room messages or return None"""
        cache_key = f"room_messages:{room_name}:{limit}"
        return self.get(cache_key)
    
    def cache_room_messages(self, room_name, messages, limit=50):
        """Cache room messages"""
        cache_key = f"room_messages:{room_name}:{limit}"
        return self.set(cache_key, messages, expire=60)  # Cache for 1 minute
    
    def invalidate_room_messages(self, room_name):
        """Invalidate cached room messages"""
        # Delete all cached message lists for this room (with any limit)
        if not self.enabled:
            return False
            
        try:
            for key in self.redis.scan_iter(f"room_messages:{room_name}:*"):
                self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis invalidate error: {e}")
            return False
    
    def get_user_data(self, username):
        """Get cached user data or return None"""
        cache_key = f"user_data:{username}"
        return self.get(cache_key)
    
    def cache_user_data(self, username, user_data):
        """Cache user data"""
        cache_key = f"user_data:{username}"
        return self.set(cache_key, user_data, expire=300)  # Cache for 5 minutes
    
    def invalidate_user_data(self, username):
        """Invalidate cached user data"""
        cache_key = f"user_data:{username}"
        return self.delete(cache_key)
    
    def get_room_metadata(self, room_name):
        """Get cached room metadata or return None"""
        cache_key = f"room_metadata:{room_name}"
        return self.get(cache_key)
    
    def cache_room_metadata(self, room_name, metadata):
        """Cache room metadata"""
        cache_key = f"room_metadata:{room_name}"
        return self.set(cache_key, metadata, expire=300)  # Cache for 5 minutes
    
    def invalidate_room_metadata(self, room_name):
        """Invalidate cached room metadata"""
        cache_key = f"room_metadata:{room_name}"
        return self.delete(cache_key)
    
    def get_active_rooms(self, limit=10):
        """Get cached active rooms or return None"""
        cache_key = f"active_rooms:{limit}"
        return self.get(cache_key)
    
    def cache_active_rooms(self, rooms, limit=10):
        """Cache active rooms"""
        cache_key = f"active_rooms:{limit}"
        return self.set(cache_key, rooms, expire=60)  # Cache for 1 minute
    
    def invalidate_active_rooms(self):
        """Invalidate all cached active room lists"""
        if not self.enabled:
            return False
            
        try:
            for key in self.redis.scan_iter("active_rooms:*"):
                self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis invalidate error: {e}")
            return False
    
    def get_analytics(self, key, days=30):
        """Get cached analytics data or return None"""
        cache_key = f"analytics:{key}:{days}"
        return self.get(cache_key)
    
    def cache_analytics(self, key, data, days=30):
        """Cache analytics data"""
        cache_key = f"analytics:{key}:{days}"
        return self.set(cache_key, data, expire=600)  # Cache for 10 minutes
    
    def invalidate_analytics(self, key=None):
        """Invalidate cached analytics data"""
        if not self.enabled:
            return False
            
        try:
            if key:
                for k in self.redis.scan_iter(f"analytics:{key}:*"):
                    self.redis.delete(k)
            else:
                for k in self.redis.scan_iter("analytics:*"):
                    self.redis.delete(k)
            return True
        except Exception as e:
            print(f"Redis invalidate error: {e}")
            return False
    
    def get_recommendations(self, username, algorithm="hybrid"):
        """Get cached recommendations or return None"""
        cache_key = f"recommendations:{username}:{algorithm}"
        return self.get(cache_key)
    
    def cache_recommendations(self, username, recommendations, algorithm="hybrid"):
        """Cache recommendations"""
        cache_key = f"recommendations:{username}:{algorithm}"
        return self.set(cache_key, recommendations, expire=300)  # Cache for 5 minutes
    
    def invalidate_recommendations(self, username=None):
        """Invalidate cached recommendations"""
        if not self.enabled:
            return False
            
        try:
            if username:
                for key in self.redis.scan_iter(f"recommendations:{username}:*"):
                    self.redis.delete(key)
            else:
                for key in self.redis.scan_iter("recommendations:*"):
                    self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis invalidate error: {e}")
            return False
    
    def store_session(self, session_id, user_data, expire_days=7):
        """Store session data in Redis"""
        if not self.enabled:
            return False
            
        try:
            # Calculate expiration time
            expire_seconds = expire_days * 24 * 60 * 60
            
            # Store session data
            cache_key = f"session:{session_id}"
            self.redis.setex(cache_key, expire_seconds, json.dumps(user_data))
            return True
        except Exception as e:
            print(f"Redis session store error: {e}")
            return False
    
    def get_session(self, session_id):
        """Get session data from Redis"""
        if not self.enabled:
            return None
            
        try:
            cache_key = f"session:{session_id}"
            data = self.redis.get(cache_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis session get error: {e}")
            return None
    
    def delete_session(self, session_id):
        """Delete session data from Redis"""
        if not self.enabled:
            return False
            
        try:
            cache_key = f"session:{session_id}"
            self.redis.delete(cache_key)
            return True
        except Exception as e:
            print(f"Redis session delete error: {e}")
            return False
    
    def store_rate_limit(self, key, limit=100, window_seconds=60):
        """Implement rate limiting using Redis"""
        if not self.enabled:
            return True  # If Redis is disabled, don't rate limit
            
        try:
            # Get current count
            current = self.redis.get(f"ratelimit:{key}")
            
            if current is None:
                # First request in this window
                self.redis.setex(f"ratelimit:{key}", window_seconds, 1)
                return True
            
            # Increment counter
            count = int(current) + 1
            
            if count > limit:
                # Rate limit exceeded
                return False
            
            # Update counter
            self.redis.setex(f"ratelimit:{key}", window_seconds, count)
            return True
        except Exception as e:
            print(f"Redis rate limit error: {e}")
            return True  # If there's an error, don't rate limit
