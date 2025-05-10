import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
import pandas as pd

class MessageSentimentAnalyzer:
    def __init__(self):
        nltk.download('vader_lexicon')
        self.sia = SentimentIntensityAnalyzer()
        
    def analyze_message(self, message):
        """Analyze the sentiment of a single message"""
        sentiment_score = self.sia.polarity_scores(message)
        return sentiment_score
    
    def analyze_conversation(self, messages):
        """Analyze sentiment trends in a conversation"""
        sentiment_scores = [self.sia.polarity_scores(msg)['compound'] for msg in messages]
        return sentiment_scores
    
    def visualize_conversation_sentiment(self, room_name):
        """Generate visualization of sentiment over time in a conversation"""
        # Read messages from room
        messages = self._get_messages_from_room(room_name)
        sentiment_scores = self.analyze_conversation(messages)
        
        # Create visualization
        df = pd.DataFrame({
            'Message Index': range(len(sentiment_scores)),
            'Sentiment': sentiment_scores
        })
        plt.figure(figsize=(10, 6))
        plt.plot(df['Message Index'], df['Sentiment'])
        plt.title(f'Conversation Sentiment Analysis for Room: {room_name}')
        plt.xlabel('Message Sequence')
        plt.ylabel('Sentiment Score')
        plt.axhline(y=0, color='r', linestyle='-')
        plt.savefig(f'{room_name}_sentiment.png')
        return f'{room_name}_sentiment.png'
    
    def _get_messages_from_room(self, room_name):
        """Extract just the message content from a room file"""
        with open(f"rooms/{room_name}.txt", "r") as f:
            lines = f.readlines()
            # Extract just the message part after the username
            messages = [line.split(':', 1)[1].strip() if ':' in line else line.strip() for line in lines]
            return messages