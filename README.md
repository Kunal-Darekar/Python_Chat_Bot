# AI-Enhanced Web Chat Application

A modern web-based chat application enhanced with advanced artificial intelligence features to provide a smarter, more engaging chat experience. This application uses MongoDB for data storage, providing improved performance, scalability, and reliability, all wrapped in an intuitive web interface.

![AI-Enhanced Chat](static/images/chat-illustration.svg)

## Features

### Modern Web Interface
- Responsive design that works on desktop and mobile devices
- Real-time message updates without page refreshes
- Interactive UI with modals, tooltips, and dynamic content
- Visualizations for sentiment analysis and user interests
- Clean, intuitive navigation and user experience

### Core Chat Functionality
- Create and join password-protected chat rooms with descriptions and tags
- Send and receive messages in real-time with timestamp tracking
- View chat history with enhanced formatting
- User authentication via room passwords
- Room categorization and metadata management
- Search and filtering capabilities

### AI Enhancements

#### 1. Advanced Sentiment Analysis
- Real-time analysis of message sentiment with compound scoring
- Visual sentiment indicators for messages
- Interactive sentiment reports with charts and graphs
- Emotional tone detection and tracking
- Identification of most positive and negative messages
- User sentiment statistics and visualization

#### 2. Multi-Algorithm Recommendation System
- Personalized room recommendations using multiple algorithms:
  - Content-based filtering using TF-IDF vectorization
  - Collaborative filtering based on user behavior
  - Topic modeling using Latent Dirichlet Allocation (LDA)
  - Hybrid recommendations combining multiple approaches
- Explanation of why rooms are recommended
- Similar room discovery
- Trending topics identification across all chat rooms
- Recommendation history tracking and analysis

#### 3. AI Chatbot Assistant
- Intelligent chatbot that can participate in conversations
- Command-based interaction system
- Conversation summarization
- Knowledge base for common questions
- Learning capabilities from user interactions

#### 4. Predictive Text
- Smart text completion as you type
- Personalized suggestions based on your writing style
- Context-aware word predictions
- Learning system that improves over time

#### 5. User Interest Profiling
- Automatic interest extraction from messages
- Interactive interest visualization with charts
- Personalized user profiles
- Activity tracking and statistics

## Technical Implementation

### Web Architecture
- Flask web framework for backend
- Bootstrap 5 for responsive frontend design
- JavaScript for interactive features
- RESTful API for client-server communication
- WebSockets for real-time updates

### MongoDB Database Architecture
- Document-based NoSQL database for flexible schema
- Collections for users, rooms, messages, and AI data
- Efficient indexing for improved query performance
- Structured data model with relationships
- Automatic backup and restore capabilities
- Advanced search and filtering functionality
- Seamless migration from previous file-based storage

### Advanced AI/ML Technologies
- Natural Language Processing (NLP) for sentiment analysis and interest extraction
- Multiple recommendation algorithms (content-based, collaborative, topic modeling)
- TF-IDF and Count vectorization for text processing
- Latent Dirichlet Allocation (LDA) for topic modeling
- N-gram models for predictive text
- Rule-based and retrieval-based chatbot system
- Interactive data visualization with Chart.js

## Getting Started

### Prerequisites
- Python 3.6 or higher
- MongoDB (local installation or MongoDB Atlas)
- Required packages:
  - Flask
  - pymongo
  - dnspython
  - python-dotenv
  - nltk
  - scikit-learn
  - matplotlib
  - numpy
  - pandas

### Installation
1. Clone the repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Configure MongoDB:
   - Create a `.env` file in the project root with the following content:
     ```
     MONGO_URI=mongodb://localhost:27017/
     DB_NAME=ai_chat_app
     SECRET_KEY=your_secret_key_here
     ```
   - For MongoDB Atlas, use the connection string provided by Atlas:
     ```
     MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
     ```
4. Run the web application:
   ```
   python app.py
   ```
   - On first run, the application will automatically migrate data from the old file-based storage to MongoDB
5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Web Interface
1. **Login**: Enter a username to identify yourself in the chat
2. **Browse Rooms**: View available chat rooms with descriptions and tags
3. **Create Room**: Create a new room with password, description, and tags
4. **Join Room**: Enter an existing room using its password
5. **Chat**: Send and receive messages in real-time
6. **AI Features**: Access sentiment analysis, recommendations, and more through the web interface

### AI Features in Web Interface
- **Sentiment Analysis**: View sentiment reports with interactive charts
- **Recommendations**: Get personalized room suggestions
- **Predictive Text**: See word suggestions as you type
- **AI Assistant**: Chat with the AI bot using @AIBot mentions
- **User Stats**: View your activity and interest profile

## Project Structure

### Backend Files
- `app.py` - Flask web application with routes and API endpoints
- `mongodb_connector.py` - MongoDB database connector with data models
- `sentiment_analyzer.py` - Sentiment analysis module with visualization
- `recommendation_system.py` - Multi-algorithm recommendation system
- `chatbot_assistant.py` - AI chatbot implementation with learning capabilities
- `predictive_text.py` - Predictive text system with personalization
- `requirements.txt` - Package dependencies
- `.env` - Environment variables for MongoDB connection

### Frontend Files
- `templates/` - HTML templates for web pages
  - `base.html` - Base template with common elements
  - `index.html` - Home page
  - `login.html` - User login page
  - `rooms.html` - Room listing page
  - `create_room.html` - Room creation form
  - `join_room.html` - Room joining form
  - `chat_room.html` - Main chat interface
- `static/` - Static assets
  - `css/style.css` - Custom styles
  - `js/main.js` - JavaScript for interactive features
  - `images/` - Images and illustrations

### Data Storage
The application uses MongoDB for data storage with the following collections:

- **`users`** - Stores user profiles, interests, and activity
- **`rooms`** - Stores room information, metadata, and settings
- **`messages`** - Stores all chat messages with timestamps and sentiment
- **`ai_data`** - Stores AI-related data like chatbot knowledge base

The application will automatically migrate data from the old file-based storage to MongoDB on first run. Backups are stored in the `backups/` directory.

## API Endpoints

The application provides a RESTful API for client-server communication:

- `GET /api/messages/<room_name>` - Get messages from a room
- `POST /api/messages/<room_name>` - Send a message to a room
- `GET /api/sentiment/<room_name>` - Get sentiment analysis for a room
- `GET /api/recommendations/<username>` - Get room recommendations
- `GET /api/trending` - Get trending topics
- `GET /api/user/<username>` - Get user statistics
- `GET /api/predict` - Get word predictions

## Advanced Features

### User Authentication
- Secure user registration and login with email and password
- Password hashing with bcrypt
- Session management with MongoDB and Redis
- User profile management
- Password reset functionality

### MongoDB Integration
- Document-based NoSQL database for flexible schema
- Collections for users, rooms, messages, and AI data
- Advanced queries with MongoDB's aggregation framework
- Efficient indexing for improved query performance
- Automatic data migration from file-based storage

### Redis Caching
- High-performance in-memory caching
- Cached room messages for faster loading
- User data caching to reduce database load
- Analytics caching for expensive computations
- Session storage for improved authentication performance
- Rate limiting implementation

### WebSockets
- Real-time message delivery without page refreshes
- User presence indicators (online/offline status)
- Typing indicators
- Join/leave notifications
- Room-based communication channels

### Cloud Deployment
- Docker containerization for consistent environments
- Docker Compose for local development
- Deployment guides for Heroku, AWS, and Azure
- Environment configuration for different platforms
- Scaling considerations for high traffic

## Future Enhancements
- Integration with external AI APIs (OpenAI, Hugging Face)
- Advanced NLP with transformer models
- Image generation from text descriptions
- Voice message transcription
- Mobile application with React Native
- User authentication with OAuth
- End-to-end encryption for messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask for the web framework
- MongoDB for the database system
- PyMongo for MongoDB integration
- Bootstrap for responsive design
- Chart.js for interactive visualizations
- NLTK for natural language processing
- Scikit-learn for machine learning components
- Matplotlib and Pandas for data visualization
- NumPy for numerical operations
