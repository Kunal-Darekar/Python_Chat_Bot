import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
import os
import json
import matplotlib.pyplot as plt
from datetime import datetime
from Database import Database

class RoomRecommender:
    def __init__(self, database=None):
        """Initialize the recommendation system with optional database instance"""
        self.db = database if database else Database()
        self.room_content = {}
        self.room_vectors = {}
        self.user_vectors = {}
        self.topic_models = {}
        self.vectorizer = TfidfVectorizer(stop_words='english', min_df=2, max_df=0.95)
        self.count_vectorizer = CountVectorizer(stop_words='english', min_df=2, max_df=0.95)
        self.lda_model = None
        self.recommendation_history = {}

        # Create directories for recommendation data
        os.makedirs('recommendation_data', exist_ok=True)

        # Load cached data if available
        self._load_cached_data()

    def update_room_content(self, force_refresh=False):
        """Update room content vectors using the database"""
        # Check if we need to refresh
        if self.room_content and not force_refresh:
            return

        self.room_content = {}

        # Get active rooms from database
        active_rooms = self.db.get_active_rooms(limit=100)

        # Get content for each room
        for room_data in active_rooms:
            room_name = room_data["name"]
            messages = self.db.get_room_messages(room_name, limit=200)

            if messages:
                # Combine all messages into a single text
                content = " ".join([msg["content"] for msg in messages])
                self.room_content[room_name] = content

        # Vectorize all room content
        if self.room_content:
            room_names = list(self.room_content.keys())
            content_texts = [self.room_content[room] for room in room_names]

            # TF-IDF vectorization
            try:
                self.content_vectors = self.vectorizer.fit_transform(content_texts)
                self.room_names = room_names

                # Update room vectors
                for i, room in enumerate(room_names):
                    self.room_vectors[room] = self.content_vectors[i]

                # Build topic model
                self._build_topic_model(content_texts)

                # Cache the data
                self._cache_data()
            except:
                # Handle case where vectorization fails (e.g., not enough data)
                self.content_vectors = None
                self.room_names = []

    def update_user_interest(self, username, message):
        """Update user interest profile based on their messages using the database"""
        # Get user interests from database
        interests = self.db.get_user_interests(username)

        # Extract keywords from message and add to interests
        # (This is now handled by the database's _update_user_interests method)

        # Update user vector
        self._update_user_vector(username)

    def get_user_recommendations(self, username, top_n=5, algorithm="hybrid"):
        """
        Get room recommendations for a user using multiple algorithms

        Args:
            username (str): The username to get recommendations for
            top_n (int): Number of recommendations to return
            algorithm (str): Algorithm to use - "content", "collaborative", "topic", or "hybrid"

        Returns:
            list: Recommended room names
        """
        # Update room content first
        self.update_room_content()

        if not self.room_content:
            return ["No active rooms found for recommendations."]

        # Get user data
        user_data = self.db.load_user_data(username)
        joined_rooms = user_data.get("joined_rooms", [])

        # Get user interests
        interests = user_data.get("interests", [])

        if not interests and not joined_rooms:
            return ["No recommendations available yet. Chat more to get personalized suggestions!"]

        # Track this recommendation request
        if username not in self.recommendation_history:
            self.recommendation_history[username] = []

        timestamp = datetime.now().isoformat()

        # Choose algorithm
        if algorithm == "content":
            recommendations = self._content_based_recommendations(username, top_n)
        elif algorithm == "collaborative":
            recommendations = self._collaborative_recommendations(username, top_n)
        elif algorithm == "topic":
            recommendations = self._topic_based_recommendations(username, top_n)
        else:  # hybrid
            recommendations = self._hybrid_recommendations(username, top_n)

        # Filter out rooms the user has already joined
        recommendations = [r for r in recommendations if r not in joined_rooms][:top_n]

        # If we don't have enough recommendations, add popular rooms
        if len(recommendations) < top_n:
            popular_rooms = self._get_popular_rooms(top_n - len(recommendations))
            for room in popular_rooms:
                if room not in recommendations and room not in joined_rooms:
                    recommendations.append(room)

        # Record recommendation
        self.recommendation_history[username].append({
            "timestamp": timestamp,
            "algorithm": algorithm,
            "recommendations": recommendations
        })

        # Save recommendation history
        self._save_recommendation_history()

        return recommendations

    def get_similar_rooms(self, room_name, top_n=5):
        """Find rooms similar to a given room"""
        self.update_room_content()

        if not self.content_vectors or room_name not in self.room_content:
            return [f"Room '{room_name}' not found."]

        # Get index of the target room
        try:
            room_idx = self.room_names.index(room_name)
        except ValueError:
            return [f"Room '{room_name}' not found in the index."]

        # Get similarity scores
        room_vector = self.content_vectors[room_idx]
        similarities = cosine_similarity(room_vector, self.content_vectors).flatten()

        # Get top N similar rooms (excluding the room itself)
        similar_indices = np.argsort(similarities)[::-1]

        # Filter out the room itself
        similar_indices = [idx for idx in similar_indices if self.room_names[idx] != room_name]

        # Get top N
        top_indices = similar_indices[:top_n]
        similar_rooms = [self.room_names[idx] for idx in top_indices]

        return similar_rooms

    def get_trending_topics(self, num_topics=5, num_words=5):
        """Get trending topics across all rooms"""
        if not self.lda_model:
            self.update_room_content(force_refresh=True)

            if not self.lda_model:
                return ["Not enough data to identify topics."]

        topics = []
        feature_names = self.count_vectorizer.get_feature_names_out()

        for topic_idx, topic in enumerate(self.lda_model.components_):
            top_features_idx = topic.argsort()[:-num_words-1:-1]
            top_features = [feature_names[i] for i in top_features_idx]
            topics.append({
                "id": topic_idx,
                "words": top_features,
                "weight": float(np.sum(topic))
            })

        # Sort by weight
        topics.sort(key=lambda x: x["weight"], reverse=True)

        return topics[:num_topics]

    def visualize_user_interests(self, username):
        """Generate visualization of user interests"""
        user_data = self.db.load_user_data(username)
        interests = user_data.get("interests", [])

        if not interests:
            return "No interests data available for visualization."

        # Get word counts if available
        word_counts = user_data.get("word_counts", {})

        if not word_counts:
            # Create counts from interests list
            word_counts = {interest: 1 for interest in interests}

        # Sort by count
        sorted_interests = sorted(
            [(word, word_counts.get(word, 1)) for word in interests],
            key=lambda x: x[1],
            reverse=True
        )

        # Create visualization
        plt.figure(figsize=(10, 6))
        words = [item[0] for item in sorted_interests]
        counts = [item[1] for item in sorted_interests]

        plt.bar(words, counts)
        plt.title(f"Interest Profile for {username}")
        plt.xlabel("Interests")
        plt.ylabel("Frequency")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # Save the visualization
        os.makedirs('analytics', exist_ok=True)
        filename = f"analytics/{username}_interests.png"
        plt.savefig(filename)
        plt.close()

        return filename

    def get_recommendation_explanation(self, username, room_name):
        """Explain why a room was recommended to a user"""
        user_data = self.db.load_user_data(username)
        interests = user_data.get("interests", [])

        if not interests:
            return "No interest data available to explain recommendations."

        # Get room metadata
        room_metadata = self.db.get_room_metadata(room_name)
        room_tags = room_metadata.get("tags", [])

        # Get room messages
        messages = self.db.get_room_messages(room_name, limit=100)
        room_content = " ".join([msg["content"] for msg in messages])

        # Find matching interests
        matching_interests = []
        for interest in interests:
            if interest.lower() in room_content.lower():
                matching_interests.append(interest)

        # Find matching tags
        matching_tags = []
        for tag in room_tags:
            if tag.lower() in [interest.lower() for interest in interests]:
                matching_tags.append(tag)

        # Generate explanation
        explanation = f"Room '{room_name}' was recommended because:\n"

        if matching_interests:
            explanation += f"- It contains content related to your interests: {', '.join(matching_interests)}\n"

        if matching_tags:
            explanation += f"- It has tags that match your interests: {', '.join(matching_tags)}\n"

        if room_metadata.get("message_count", 0) > 0:
            explanation += f"- It's an active room with {room_metadata['message_count']} messages\n"

        if not matching_interests and not matching_tags:
            explanation += "- It's a popular room that might interest you based on your activity\n"

        return explanation

    def _content_based_recommendations(self, username, top_n=5):
        """Get content-based recommendations using TF-IDF and cosine similarity"""
        # Get user interests
        user_data = self.db.load_user_data(username)
        interests = user_data.get("interests", [])

        if not interests or not self.content_vectors:
            return []

        # Create user vector from interests
        user_text = " ".join(interests)
        try:
            user_vector = self.vectorizer.transform([user_text])
        except:
            # If vectorization fails, return empty list
            return []

        # Calculate similarity with all rooms
        similarities = cosine_similarity(user_vector, self.content_vectors).flatten()

        # Get top N recommendations
        top_indices = similarities.argsort()[-top_n*2:][::-1]  # Get more than needed for filtering
        recommendations = [self.room_names[i] for i in top_indices]

        return recommendations

    def _collaborative_recommendations(self, username, top_n=5):
        """Get collaborative filtering recommendations based on user activity"""
        # Get rooms the user has joined
        user_data = self.db.load_user_data(username)
        user_rooms = set(user_data.get("joined_rooms", []))

        if not user_rooms:
            return []

        # Find users with similar room preferences
        similar_users = []

        # Get all user data files
        user_files = [f for f in os.listdir('user_data') if f.endswith('.json')]

        for user_file in user_files:
            other_username = user_file[:-5]  # Remove .json extension

            if other_username == username:
                continue

            try:
                with open(os.path.join('user_data', user_file), 'r') as f:
                    other_data = json.load(f)

                other_rooms = set(other_data.get("joined_rooms", []))

                # Calculate Jaccard similarity
                if other_rooms:
                    intersection = len(user_rooms.intersection(other_rooms))
                    union = len(user_rooms.union(other_rooms))

                    if union > 0:
                        similarity = intersection / union

                        similar_users.append({
                            "username": other_username,
                            "similarity": similarity,
                            "rooms": list(other_rooms)
                        })
            except:
                continue

        # Sort by similarity
        similar_users.sort(key=lambda x: x["similarity"], reverse=True)

        # Get recommendations from similar users
        recommendations = []
        room_scores = {}

        for user in similar_users[:10]:  # Consider top 10 similar users
            for room in user["rooms"]:
                if room not in user_rooms:
                    if room not in room_scores:
                        room_scores[room] = 0

                    room_scores[room] += user["similarity"]

        # Sort rooms by score
        sorted_rooms = sorted(room_scores.items(), key=lambda x: x[1], reverse=True)
        recommendations = [room for room, score in sorted_rooms[:top_n]]

        return recommendations

    def _topic_based_recommendations(self, username, top_n=5):
        """Get recommendations based on topic modeling"""
        if not self.lda_model:
            return []

        # Get user interests
        user_data = self.db.load_user_data(username)
        interests = user_data.get("interests", [])

        if not interests:
            return []

        # Create user vector from interests
        user_text = " ".join(interests)
        try:
            user_count_vector = self.count_vectorizer.transform([user_text])
            user_topic_dist = self.lda_model.transform(user_count_vector)[0]
        except:
            return []

        # Get topic distribution for each room
        room_topic_dists = {}
        for room_name in self.room_names:
            room_text = self.room_content[room_name]
            try:
                room_count_vector = self.count_vectorizer.transform([room_text])
                room_topic_dist = self.lda_model.transform(room_count_vector)[0]
                room_topic_dists[room_name] = room_topic_dist
            except:
                continue

        # Calculate similarity between user and room topic distributions
        room_scores = {}
        for room_name, room_topic_dist in room_topic_dists.items():
            # Use Jensen-Shannon divergence
            similarity = 1.0 - np.sqrt(0.5 * np.sum((user_topic_dist - room_topic_dist)**2))
            room_scores[room_name] = similarity

        # Sort rooms by score
        sorted_rooms = sorted(room_scores.items(), key=lambda x: x[1], reverse=True)
        recommendations = [room for room, score in sorted_rooms[:top_n]]

        return recommendations

    def _hybrid_recommendations(self, username, top_n=5):
        """Combine multiple recommendation approaches"""
        # Get recommendations from each method
        content_recs = self._content_based_recommendations(username, top_n)
        collab_recs = self._collaborative_recommendations(username, top_n)
        topic_recs = self._topic_based_recommendations(username, top_n)

        # Combine and weight recommendations
        room_scores = {}

        # Content-based (weight: 0.4)
        for i, room in enumerate(content_recs):
            if room not in room_scores:
                room_scores[room] = 0
            room_scores[room] += 0.4 * (1.0 - (i / len(content_recs)))

        # Collaborative (weight: 0.4)
        for i, room in enumerate(collab_recs):
            if room not in room_scores:
                room_scores[room] = 0
            room_scores[room] += 0.4 * (1.0 - (i / len(collab_recs)))

        # Topic-based (weight: 0.2)
        for i, room in enumerate(topic_recs):
            if room not in room_scores:
                room_scores[room] = 0
            room_scores[room] += 0.2 * (1.0 - (i / len(topic_recs)))

        # Sort rooms by score
        sorted_rooms = sorted(room_scores.items(), key=lambda x: x[1], reverse=True)
        recommendations = [room for room, score in sorted_rooms[:top_n]]

        return recommendations

    def _get_popular_rooms(self, limit=5):
        """Get most popular rooms based on message count"""
        active_rooms = self.db.get_active_rooms(limit=limit*2)

        # Sort by message count
        active_rooms.sort(key=lambda x: x["message_count"], reverse=True)

        return [room["name"] for room in active_rooms[:limit]]

    def _update_user_vector(self, username):
        """Update vector representation of user interests"""
        # Get user interests
        interests = self.db.get_user_interests(username)

        if not interests:
            return

        # Create vector from interests
        user_text = " ".join(interests)
        try:
            user_vector = self.vectorizer.transform([user_text])
            self.user_vectors[username] = user_vector
        except:
            pass

    def _build_topic_model(self, texts, num_topics=10):
        """Build LDA topic model from room content"""
        if not texts or len(texts) < 3:
            return

        try:
            # Create document-term matrix
            dtm = self.count_vectorizer.fit_transform(texts)

            # Build LDA model
            self.lda_model = LatentDirichletAllocation(
                n_components=min(num_topics, len(texts)),
                max_iter=10,
                learning_method='online',
                random_state=42,
                batch_size=128,
                evaluate_every=-1
            )

            self.lda_model.fit(dtm)
        except:
            self.lda_model = None

    def _cache_data(self):
        """Cache vectorizer and other data for faster loading"""
        try:
            cache_file = os.path.join('recommendation_data', 'cache_info.json')
            with open(cache_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "num_rooms": len(self.room_names),
                    "vectorizer_features": len(self.vectorizer.get_feature_names_out())
                }, f)
        except:
            pass

    def _load_cached_data(self):
        """Load cached recommendation history"""
        try:
            history_file = os.path.join('recommendation_data', 'recommendation_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.recommendation_history = json.load(f)
        except:
            self.recommendation_history = {}

    def _save_recommendation_history(self):
        """Save recommendation history to file"""
        try:
            history_file = os.path.join('recommendation_data', 'recommendation_history.json')
            with open(history_file, 'w') as f:
                json.dump(self.recommendation_history, f, indent=2)
        except:
            pass