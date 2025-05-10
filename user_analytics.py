# Create a new file: user_analytics.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns
from sklearn.cluster import KMeans

class UserAnalytics:
    def __init__(self):
        self.user_data = {}
        
    def track_user_activity(self, username, room, action, message=None):
        """Record user activity for analysis"""
        timestamp = datetime.now()
        
        if username not in self.user_data:
            self.user_data[username] = []
            
        activity = {
            'timestamp': timestamp,
            'room': room,
            'action': action,  # 'join', 'leave', 'message', 'create_room'
            'message_length': len(message) if message else 0,
            'hour_of_day': timestamp.hour
        }
        
        self.user_data[username].append(activity)
        
        # Save data periodically
        if len(self.user_data[username]) % 10 == 0:
            self._save_user_data()
            
    def _save_user_data(self):
        """Save user data to CSV file"""
        all_data = []
        for username, activities in self.user_data.items():
            for activity in activities:
                row = {
                    'username': username,
                    'timestamp': activity['timestamp'],
                    'room': activity['room'],
                    'action': activity['action'],
                    'message_length': activity['message_length'],
                    'hour_of_day': activity['hour_of_day']
                }
                all_data.append(row)
                
        df = pd.DataFrame(all_data)
        df.to_csv('user_activity_data.csv', index=False)
        
    def generate_user_report(self, username):
        """Generate analytics report for a specific user"""
        if username not in self.user_data or not self.user_data[username]:
            return f"No data available for user {username}"
            
        # Convert user data to DataFrame
        user_df = pd.DataFrame(self.user_data[username])
        
        # Basic statistics
        total_messages = sum(1 for activity in self.user_data[username] if activity['action'] == 'message')
        avg_message_length = user_df[user_df['action'] == 'message']['message_length'].mean()
        active_rooms = user_df['room'].nunique()
        most_active_room = user_df['room'].value_counts().idxmax()
        
        # Activity by hour
        hour_activity = user_df['hour_of_day'].value_counts().sort_index()
        
        # Create visualizations
        plt.figure(figsize=(12, 8))
        
        # Activity by hour chart
        plt.subplot(2, 1, 1)
        sns.barplot(x=hour_activity.index, y=hour_activity.values)
        plt.title(f'Activity by Hour for {username}')
        plt.xlabel('Hour of Day')
        plt.ylabel('Number of Actions')
        
        # Message length over time
        plt.subplot(2, 1, 2)
        message_df = user_df[user_df['action'] == 'message']
        plt.plot(range(len(message_df)), message_df['message_length'])
        plt.title(f'Message Length Over Time for {username}')
        plt.xlabel('Message Sequence')
        plt.ylabel('Message Length (chars)')
        
        # Save the figure
        plt.tight_layout()
        report_filename = f'{username}_analytics.png'
        plt.savefig(report_filename)
        
        # Generate text report
        report = f"""
        User Analytics Report for {username}
        ===================================
        Total messages sent: {total_messages}
        Average message length: {avg_message_length:.2f} characters
        Active in {active_rooms} rooms
        Most active room: {most_active_room}
        
        A visualization has been saved to {report_filename}
        """
        
        return report
        
    def cluster_users(self, num_clusters=3):
        """Group users by behavior patterns"""
        # Prepare features for clustering
        user_features = []
        usernames = []
        
        for username, activities in self.user_data.items():
            if not activities:
                continue
                
            # Convert to DataFrame for easier analysis
            user_df = pd.DataFrame(activities)
            
            # Extract features
            avg_message_length = user_df[user_df['action'] == 'message']['message_length'].mean()
            message_count = sum(1 for a in activities if a['action'] == 'message')
            room_count = user_df['room'].nunique()
            
            # Get active hours (0-23)
            active_hours = user_df['hour_of_day'].value_counts()
            hour_features = np.zeros(24)
            for hour, count in active_hours.items():
                hour_features[hour] = count
                
            # Combine features
            features = [avg_message_length, message_count, room_count]
            features.extend(hour_features)
            
            user_features.append(features)
            usernames.append(username)
            
        if not user_features:
            return "Not enough user data for clustering"
            
        # Apply K-means clustering
        X = np.array(user_features)
        kmeans = KMeans(n_clusters=min(num_clusters, len(X)), random_state=42)
        clusters = kmeans.fit_predict(X)
        
        # Create report
        cluster_report = "User Behavior Clusters\n=====================\n"
        for i in range(min(num_clusters, len(X))):
            users_in_cluster = [usernames[j] for j in range(len(usernames)) if clusters[j] == i]
            cluster_report += f"\nCluster {i+1}:\n"
            cluster_report += f"Users: {', '.join(users_in_cluster)}\n"
            
            # Describe cluster characteristics
            cluster_features = X[clusters == i]
            avg_features = np.mean(cluster_features, axis=0)
            
            cluster_report += f"Average message length: {avg_features[0]:.2f}\n"
            cluster_report += f"Average message count: {avg_features[1]:.2f}\n"
            cluster_report += f"Average number of rooms: {avg_features[2]:.2f}\n"
            
            # Most active hours
            hour_activity = avg_features[3:27]
            top_hours = np.argsort(hour_activity)[-3:][::-1]
            cluster_report += f"Most active hours: {', '.join(str(h) for h in top_hours)}\n"
            
        return cluster_report