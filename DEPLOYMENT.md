# Deployment Guide

This guide provides instructions for deploying the AI-Enhanced Chat Application to various cloud platforms.

## Prerequisites

- Git repository with your application code
- MongoDB Atlas account (or other MongoDB hosting)
- Redis Cloud account (optional, for caching)
- Account on your chosen cloud platform (Heroku, AWS, Azure, etc.)

## Environment Variables

The following environment variables need to be set in your deployment environment:

```
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
DB_NAME=ai_chat_app
REDIS_URL=redis://:<password>@<host>:<port>
SECRET_KEY=<your_secret_key>
```

## Deployment Options

### 1. Heroku Deployment

1. **Install Heroku CLI**:
   ```
   npm install -g heroku
   ```

2. **Login to Heroku**:
   ```
   heroku login
   ```

3. **Create a new Heroku app**:
   ```
   heroku create ai-enhanced-chat
   ```

4. **Add MongoDB and Redis add-ons**:
   ```
   heroku addons:create mongolab
   heroku addons:create heroku-redis
   ```

5. **Set environment variables**:
   ```
   heroku config:set SECRET_KEY=your_secret_key_here
   ```

6. **Deploy the application**:
   ```
   git push heroku main
   ```

7. **Open the application**:
   ```
   heroku open
   ```

### 2. AWS Elastic Beanstalk Deployment

1. **Install AWS CLI and EB CLI**:
   ```
   pip install awscli awsebcli
   ```

2. **Configure AWS credentials**:
   ```
   aws configure
   ```

3. **Initialize EB application**:
   ```
   eb init -p python-3.8 ai-enhanced-chat
   ```

4. **Create an environment**:
   ```
   eb create ai-enhanced-chat-env
   ```

5. **Set environment variables**:
   ```
   eb setenv MONGO_URI=mongodb+srv://... DB_NAME=ai_chat_app REDIS_URL=redis://... SECRET_KEY=...
   ```

6. **Deploy the application**:
   ```
   eb deploy
   ```

7. **Open the application**:
   ```
   eb open
   ```

### 3. Azure App Service Deployment

1. **Install Azure CLI**:
   ```
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Login to Azure**:
   ```
   az login
   ```

3. **Create a resource group**:
   ```
   az group create --name ai-chat-group --location eastus
   ```

4. **Create an App Service plan**:
   ```
   az appservice plan create --name ai-chat-plan --resource-group ai-chat-group --sku B1 --is-linux
   ```

5. **Create a web app**:
   ```
   az webapp create --resource-group ai-chat-group --plan ai-chat-plan --name ai-enhanced-chat --runtime "PYTHON|3.9"
   ```

6. **Set environment variables**:
   ```
   az webapp config appsettings set --resource-group ai-chat-group --name ai-enhanced-chat --settings MONGO_URI="mongodb+srv://..." DB_NAME="ai_chat_app" REDIS_URL="redis://..." SECRET_KEY="..."
   ```

7. **Deploy the application**:
   ```
   az webapp deployment source config-local-git --name ai-enhanced-chat --resource-group ai-chat-group
   git remote add azure <git-url-from-previous-command>
   git push azure main
   ```

### 4. Docker Deployment

1. **Build the Docker image**:
   ```
   docker build -t ai-enhanced-chat .
   ```

2. **Run the Docker container**:
   ```
   docker run -p 8080:8080 \
     -e MONGO_URI="mongodb+srv://..." \
     -e DB_NAME="ai_chat_app" \
     -e REDIS_URL="redis://..." \
     -e SECRET_KEY="..." \
     ai-enhanced-chat
   ```

3. **Using Docker Compose**:
   ```
   docker-compose up -d
   ```

## Scaling Considerations

### MongoDB Scaling

1. **Indexing**: Ensure proper indexes are created for frequently queried fields.
2. **Sharding**: For large datasets, consider enabling sharding in MongoDB Atlas.
3. **Read Replicas**: Use read replicas for read-heavy workloads.

### Redis Caching

1. **Cache Expiration**: Set appropriate expiration times for cached data.
2. **Memory Management**: Monitor Redis memory usage and adjust maxmemory settings.
3. **Persistence**: Configure Redis persistence for data durability.

### Application Scaling

1. **Horizontal Scaling**: Deploy multiple instances of the application behind a load balancer.
2. **WebSocket Scaling**: For WebSocket support, ensure your platform supports sticky sessions.
3. **Static Assets**: Use a CDN for static assets to reduce server load.

## Monitoring and Maintenance

1. **Logging**: Set up centralized logging with services like Papertrail or Loggly.
2. **Monitoring**: Use monitoring tools like New Relic, Datadog, or CloudWatch.
3. **Backups**: Regularly backup your MongoDB data.
4. **Updates**: Keep dependencies updated for security and performance improvements.

## Troubleshooting

1. **Connection Issues**: Verify network connectivity and security group settings.
2. **Memory Errors**: Check for memory leaks and adjust container memory limits.
3. **Slow Performance**: Analyze database queries and implement caching for slow operations.
4. **WebSocket Issues**: Ensure your platform and load balancer support WebSocket connections.

## Security Considerations

1. **HTTPS**: Always use HTTPS in production.
2. **Environment Variables**: Never commit sensitive information to your repository.
3. **Input Validation**: Validate all user inputs to prevent injection attacks.
4. **Authentication**: Implement proper user authentication and authorization.
5. **Rate Limiting**: Implement rate limiting to prevent abuse.
