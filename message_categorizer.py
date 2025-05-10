# Create a new file: message_categorizer.py
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

class MessageCategorizer:
    def __init__(self):
        nltk.download('punkt')
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
    def preprocess_text(self, text):
        """Tokenize and remove stopwords"""
        tokens = word_tokenize(text.lower())
        filtered_tokens = [w for w in tokens if w not in self.stop_words]
        return " ".join(filtered_tokens)
    
    def categorize_messages(self, messages, num_categories=5):
        """Group messages into categories using K-means clustering"""
        # Preprocess messages
        processed_messages = [self.preprocess_text(msg) for msg in messages]
        
        # Vectorize the messages
        X = self.vectorizer.fit_transform(processed_messages)
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=num_categories, random_state=42)
        kmeans.fit(X)
        
        # Get cluster assignments
        clusters = kmeans.labels_
        
        # Get top terms per cluster
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
        terms = self.vectorizer.get_feature_names_out()
        
        # Create category descriptions
        categories = {}
        for i in range(num_categories):
            category_terms = [terms[ind] for ind in order_centroids[i, :5]]
            categories[i] = f"Category {i}: {', '.join(category_terms)}"
        
        # Assign categories to messages
        categorized_messages = [(messages[i], clusters[i], categories[clusters[i]]) 
                               for i in range(len(messages))]
        
        return categorized_messages, categories