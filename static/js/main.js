document.addEventListener('DOMContentLoaded', function() {
    // User stats modal
    const userStatsLink = document.getElementById('userStatsLink');
    if (userStatsLink) {
        userStatsLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            const username = document.querySelector('.dropdown-toggle').textContent.trim();
            const userStatsModal = new bootstrap.Modal(document.getElementById('userStatsModal'));
            userStatsModal.show();
            
            // Load user stats
            fetch(`/api/user/${username}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('userStatsContent').innerHTML = `
                            <div class="alert alert-danger">
                                <i class="bi bi-exclamation-triangle me-2"></i>${data.error}
                            </div>
                        `;
                        return;
                    }
                    
                    displayUserStats(data);
                })
                .catch(error => {
                    console.error('Error loading user stats:', error);
                    document.getElementById('userStatsContent').innerHTML = `
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle me-2"></i>Failed to load user statistics. Please try again.
                        </div>
                    `;
                });
        });
    }
    
    // User interests modal
    const userInterestsLink = document.getElementById('userInterestsLink');
    if (userInterestsLink) {
        userInterestsLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            const username = document.querySelector('.dropdown-toggle').textContent.trim();
            const userInterestsModal = new bootstrap.Modal(document.getElementById('userInterestsModal'));
            userInterestsModal.show();
            
            // Load user interests
            fetch(`/api/user/${username}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('userInterestsContent').innerHTML = `
                            <div class="alert alert-danger">
                                <i class="bi bi-exclamation-triangle me-2"></i>${data.error}
                            </div>
                        `;
                        return;
                    }
                    
                    displayUserInterests(data);
                })
                .catch(error => {
                    console.error('Error loading user interests:', error);
                    document.getElementById('userInterestsContent').innerHTML = `
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle me-2"></i>Failed to load user interests. Please try again.
                        </div>
                    `;
                });
        });
    }
    
    // Display user stats
    function displayUserStats(data) {
        const container = document.getElementById('userStatsContent');
        
        // Create stats HTML
        let html = `
            <div class="row">
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0"><i class="bi bi-person-badge me-2"></i>User Info</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>Username:</strong> ${data.username}</p>
                            <p><strong>Messages Sent:</strong> ${data.messages_sent}</p>
                            <p><strong>Rooms Joined:</strong> ${data.joined_rooms.length}</p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0"><i class="bi bi-emoji-smile me-2"></i>Sentiment Stats</h5>
                        </div>
                        <div class="card-body">
                            <canvas id="sentimentStatsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card mb-3">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="bi bi-chat-square-dots me-2"></i>Joined Rooms</h5>
                </div>
                <div class="card-body">
                    <div class="list-group">
        `;
        
        if (data.joined_rooms.length === 0) {
            html += `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>You haven't joined any rooms yet.
                </div>
            `;
        } else {
            data.joined_rooms.forEach(room => {
                html += `
                    <a href="/chat/${room.name}" class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${room.name}</h6>
                            <small>${room.message_count} messages</small>
                        </div>
                        ${room.description ? `<small>${room.description}</small>` : ''}
                    </a>
                `;
            });
        }
        
        html += `
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
        // Create sentiment chart if data exists
        if (data.sentiment_stats && Object.keys(data.sentiment_stats).length > 0) {
            const ctx = document.getElementById('sentimentStatsChart').getContext('2d');
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(data.sentiment_stats).map(key => key.charAt(0).toUpperCase() + key.slice(1)),
                    datasets: [{
                        data: Object.values(data.sentiment_stats),
                        backgroundColor: [
                            '#20c997', // Positive
                            '#6c757d', // Neutral
                            '#dc3545'  // Negative
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        },
                        title: {
                            display: true,
                            text: 'Message Sentiment'
                        }
                    }
                }
            });
        }
    }
    
    // Display user interests
    function displayUserInterests(data) {
        const container = document.getElementById('userInterestsContent');
        
        if (!data.interests || data.interests.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>No interests detected yet. Chat more to build your interest profile!
                </div>
            `;
            return;
        }
        
        // Create interests visualization
        container.innerHTML = `
            <div class="mb-4">
                <canvas id="interestsChart"></canvas>
            </div>
            
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="bi bi-tags me-2"></i>Your Interests</h5>
                </div>
                <div class="card-body">
                    <div class="d-flex flex-wrap gap-2">
                        ${data.interests.map(interest => 
                            `<span class="badge bg-primary">${interest}</span>`
                        ).join('')}
                    </div>
                </div>
                <div class="card-footer">
                    <small class="text-muted">These interests are automatically detected from your messages.</small>
                </div>
            </div>
        `;
        
        // Create interests chart
        const ctx = document.getElementById('interestsChart').getContext('2d');
        
        // Limit to top 10 interests for the chart
        const topInterests = data.interests.slice(0, 10);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: topInterests,
                datasets: [{
                    label: 'Interest Strength',
                    data: topInterests.map((_, i) => 10 - i), // Simulate decreasing strength
                    backgroundColor: 'rgba(13, 110, 253, 0.7)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Top Interests'
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Relevance'
                        }
                    }
                }
            }
        });
    }
});
