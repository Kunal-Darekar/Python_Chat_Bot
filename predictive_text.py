import os
import json
import re
from collections import Counter, defaultdict

class PredictiveText:
    """Simple predictive text system based on n-grams"""
    
    def __init__(self):
        self.user_models = {}
        self.global_model = defaultdict(Counter)
        self.load_models()
        
        # Create directory if it doesn't exist
        os.makedirs('predictive_models', exist_ok=True)
    
    def load_models(self):
        """Load existing predictive models"""
        # Load global model
        try:
            with open('predictive_models/global_model.json', 'r') as f:
                model_data = json.load(f)
                for prefix, continuations in model_data.items():
                    self.global_model[prefix] = Counter(continuations)
        except (FileNotFoundError, json.JSONDecodeError):
            self.global_model = defaultdict(Counter)
        
        # Load user-specific models
        try:
            user_files = [f for f in os.listdir('predictive_models') 
                         if f.endswith('_model.json') and not f.startswith('global')]
            
            for user_file in user_files:
                username = user_file.replace('_model.json', '')
                with open(f'predictive_models/{user_file}', 'r') as f:
                    model_data = json.load(f)
                    user_model = defaultdict(Counter)
                    for prefix, continuations in model_data.items():
                        user_model[prefix] = Counter(continuations)
                    self.user_models[username] = user_model
        except (FileNotFoundError, OSError):
            pass
    
    def save_models(self):
        """Save predictive models to disk"""
        # Save global model
        with open('predictive_models/global_model.json', 'w') as f:
            # Convert defaultdict and Counter to regular dict for JSON serialization
            model_data = {prefix: dict(counter) for prefix, counter in self.global_model.items()}
            json.dump(model_data, f, indent=2)
        
        # Save user-specific models
        for username, model in self.user_models.items():
            with open(f'predictive_models/{username}_model.json', 'w') as f:
                model_data = {prefix: dict(counter) for prefix, counter in model.items()}
                json.dump(model_data, f, indent=2)
    
    def train_on_message(self, username, message):
        """Update models with new message data"""
        # Ensure user has a model
        if username not in self.user_models:
            self.user_models[username] = defaultdict(Counter)
        
        # Clean and tokenize the message
        words = self._tokenize_message(message)
        
        # Skip if too few words
        if len(words) < 2:
            return
        
        # Update models with n-grams (using bigrams and trigrams)
        # Bigrams (pairs of words)
        for i in range(len(words) - 1):
            prefix = words[i]
            next_word = words[i + 1]
            
            # Update global model
            self.global_model[prefix][next_word] += 1
            
            # Update user model
            self.user_models[username][prefix][next_word] += 1
        
        # Trigrams (three words)
        for i in range(len(words) - 2):
            prefix = f"{words[i]} {words[i + 1]}"
            next_word = words[i + 2]
            
            # Update global model
            self.global_model[prefix][next_word] += 1
            
            # Update user model
            self.user_models[username][prefix][next_word] += 1
        
        # Save models periodically (could be optimized to save less frequently)
        self.save_models()
    
    def predict_next_word(self, username, current_text, max_suggestions=3):
        """Predict the next word based on current text"""
        if not current_text:
            return []
        
        # Get the last word or phrase to use as prefix
        words = self._tokenize_message(current_text)
        
        suggestions = []
        
        # Try to match the last two words (trigram)
        if len(words) >= 2:
            prefix = f"{words[-2]} {words[-1]}"
            suggestions = self._get_suggestions(username, prefix, max_suggestions)
        
        # If we don't have enough suggestions, try with just the last word (bigram)
        if len(suggestions) < max_suggestions and words:
            prefix = words[-1]
            additional_suggestions = self._get_suggestions(username, prefix, 
                                                         max_suggestions - len(suggestions))
            suggestions.extend([s for s in additional_suggestions if s not in suggestions])
        
        return suggestions[:max_suggestions]
    
    def _get_suggestions(self, username, prefix, max_count):
        """Get word suggestions for a prefix from user and global models"""
        suggestions = []
        
        # First check user-specific model (higher priority)
        if username in self.user_models and prefix in self.user_models[username]:
            user_suggestions = self.user_models[username][prefix].most_common(max_count)
            suggestions.extend([word for word, _ in user_suggestions])
        
        # Then check global model for additional suggestions
        if prefix in self.global_model and len(suggestions) < max_count:
            global_suggestions = self.global_model[prefix].most_common(max_count * 2)  # Get more for filtering
            for word, _ in global_suggestions:
                if word not in suggestions and len(suggestions) < max_count:
                    suggestions.append(word)
        
        return suggestions
    
    def _tokenize_message(self, message):
        """Clean and tokenize a message into words"""
        # Convert to lowercase and split into words
        message = message.lower()
        # Remove special characters but keep apostrophes for contractions
        message = re.sub(r'[^\w\s\']', ' ', message)
        # Split on whitespace
        words = message.split()
        return words
