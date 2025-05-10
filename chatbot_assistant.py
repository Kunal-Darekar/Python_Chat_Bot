import random
import re
import json
import os
from datetime import datetime

class ChatbotAssistant:
    """Simple rule-based chatbot assistant for the chat application"""

    def __init__(self, name="AIBot", db=None):
        self.name = name
        self.db = db  # MongoDB connector instance
        self.knowledge_base = self._load_knowledge_base()
        self.conversation_history = {}

    def _load_knowledge_base(self):
        """Load or initialize knowledge base"""
        # Try to load from MongoDB if available
        if self.db:
            try:
                kb = self.db.load_ai_data("knowledge_base")
                if kb:
                    return kb
            except Exception as e:
                print(f"Error loading knowledge base from MongoDB: {e}")

        # Fallback to file-based storage
        try:
            os.makedirs('chatbot_data', exist_ok=True)
            knowledge_base_path = 'chatbot_data/knowledge_base.json'

            with open(knowledge_base_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Initialize with some basic QA pairs
            basic_knowledge = {
                "greeting": [
                    "Hello! How can I help you today?",
                    "Hi there! I'm your chat assistant.",
                    "Greetings! How's your day going?"
                ],
                "farewell": [
                    "Goodbye! Have a great day!",
                    "See you later!",
                    "Bye! Come back soon!"
                ],
                "thanks": [
                    "You're welcome!",
                    "Happy to help!",
                    "No problem at all!"
                ],
                "help": [
                    "I can help with: \n- Answering questions\n- Providing room recommendations\n- Summarizing conversations\nJust ask me anything!",
                    "Need help? I can answer questions, recommend rooms, or just chat!"
                ],
                "about": [
                    f"I'm {self.name}, an AI assistant for this chat application. I'm here to help make your chat experience better!"
                ],
                "weather": [
                    "I don't have real-time weather data, but I can pretend! It's sunny with a chance of AI."
                ],
                "joke": [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "What do you call fake spaghetti? An impasta!",
                    "Why did the chatbot go to therapy? It had too many issues to process!"
                ]
            }

            # Save the knowledge base
            try:
                # Save to MongoDB if available
                if self.db:
                    self.db.save_ai_data("knowledge_base", basic_knowledge)
                else:
                    # Fallback to file-based storage
                    with open(knowledge_base_path, 'w') as f:
                        json.dump(basic_knowledge, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save knowledge base: {e}")

            return basic_knowledge

    def get_response(self, user_input, room_name, username):
        """Generate a response to user input"""
        # Track conversation history
        if room_name not in self.conversation_history:
            self.conversation_history[room_name] = []

        self.conversation_history[room_name].append({
            "user": username,
            "message": user_input,
            "timestamp": datetime.now().isoformat()
        })

        # Process commands
        if user_input.startswith("/"):
            return self._process_command(user_input, room_name, username)

        # Process regular messages
        user_input_lower = user_input.lower()

        # Check for greetings
        if any(word in user_input_lower for word in ["hello", "hi", "hey", "greetings"]):
            return random.choice(self.knowledge_base["greeting"])

        # Check for farewells
        if any(word in user_input_lower for word in ["bye", "goodbye", "see you", "later"]):
            return random.choice(self.knowledge_base["farewell"])

        # Check for thanks
        if any(word in user_input_lower for word in ["thanks", "thank you", "appreciate"]):
            return random.choice(self.knowledge_base["thanks"])

        # Check for help request
        if any(word in user_input_lower for word in ["help", "assist", "support"]):
            return random.choice(self.knowledge_base["help"])

        # Check for questions about the bot
        if any(phrase in user_input_lower for phrase in ["who are you", "what are you", "about you"]):
            return random.choice(self.knowledge_base["about"])

        # Check for weather questions
        if any(word in user_input_lower for word in ["weather", "temperature", "forecast"]):
            return random.choice(self.knowledge_base["weather"])

        # Check for joke requests
        if any(word in user_input_lower for word in ["joke", "funny", "laugh"]):
            return random.choice(self.knowledge_base["joke"])

        # Default responses if nothing matches
        default_responses = [
            "Interesting! Tell me more about that.",
            "I'm not sure I understand. Could you explain differently?",
            "That's a good point. What else is on your mind?",
            "I'm still learning. Can you tell me more?",
            f"I don't have enough information about that yet. Would you like to teach {self.name} about this topic?"
        ]

        return random.choice(default_responses)

    def _process_command(self, command, room_name, username):
        """Process special commands starting with /"""
        # Help command
        if command.lower() == "/help":
            return """
            Available commands:
            /help - Show this help message
            /joke - Tell a random joke
            /summary - Summarize recent conversation
            /learn [topic] [information] - Teach me something new
            /stats - Show chat statistics
            """

        # Joke command
        if command.lower() == "/joke":
            return random.choice(self.knowledge_base["joke"])

        # Summary command
        if command.lower() == "/summary":
            return self._generate_summary(room_name)

        # Learn command
        learn_match = re.match(r"/learn\s+(\w+)\s+(.*)", command)
        if learn_match:
            topic = learn_match.group(1).lower()
            information = learn_match.group(2)
            return self._learn_new_information(topic, information)

        # Stats command
        if command.lower() == "/stats":
            return self._generate_stats(room_name)

        # Unknown command
        return f"Unknown command: {command}. Type /help for available commands."

    def _generate_summary(self, room_name):
        """Generate a simple summary of recent conversation"""
        if room_name not in self.conversation_history or len(self.conversation_history[room_name]) < 3:
            return "Not enough conversation to summarize yet."

        # Get recent messages
        recent_messages = self.conversation_history[room_name][-10:]

        # Count messages per user
        user_counts = {}
        for msg in recent_messages:
            user = msg["user"]
            if user not in user_counts:
                user_counts[user] = 0
            user_counts[user] += 1

        # Generate summary
        summary = f"Summary of recent conversation in {room_name}:\n"
        summary += f"- {len(recent_messages)} messages in the recent discussion\n"
        summary += f"- Participants: {', '.join(user_counts.keys())}\n"
        summary += f"- Most active: {max(user_counts.items(), key=lambda x: x[1])[0]}\n"

        # Add topic detection (very simple version)
        all_text = " ".join([msg["message"] for msg in recent_messages])
        words = re.findall(r'\b\w+\b', all_text.lower())
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                if word not in word_counts:
                    word_counts[word] = 0
                word_counts[word] += 1

        # Get top words
        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_words:
            summary += f"- Main topics: {', '.join(word[0] for word in top_words)}\n"

        return summary

    def _learn_new_information(self, topic, information):
        """Add new information to the knowledge base"""
        if topic in self.knowledge_base:
            self.knowledge_base[topic].append(information)
        else:
            self.knowledge_base[topic] = [information]

        # Save updated knowledge base
        try:
            # Save to MongoDB if available
            if self.db:
                self.db.save_ai_data("knowledge_base", self.knowledge_base)
            else:
                # Fallback to file-based storage
                with open('chatbot_data/knowledge_base.json', 'w') as f:
                    json.dump(self.knowledge_base, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save knowledge base: {e}")

        return f"Thanks! I've learned something new about {topic}."

    def _generate_stats(self, room_name):
        """Generate simple statistics about the chat room"""
        if room_name not in self.conversation_history or not self.conversation_history[room_name]:
            return "No chat statistics available for this room yet."

        messages = self.conversation_history[room_name]

        # Count messages per user
        user_counts = {}
        for msg in messages:
            user = msg["user"]
            if user not in user_counts:
                user_counts[user] = 0
            user_counts[user] += 1

        # Calculate average message length
        avg_length = sum(len(msg["message"]) for msg in messages) / len(messages)

        # Generate stats
        stats = f"Chat Statistics for {room_name}:\n"
        stats += f"- Total messages: {len(messages)}\n"
        stats += f"- Average message length: {avg_length:.1f} characters\n"
        stats += f"- Participants: {len(user_counts)}\n"
        stats += "- Messages per user:\n"

        for user, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True):
            stats += f"  - {user}: {count} messages\n"

        return stats
