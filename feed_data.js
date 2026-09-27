const statusFeed = [
    { id: 1, type: 'info', message: 'System initialized.', timestamp: new Date().toISOString() },
    { id: 2, type: 'success', message: 'Inventory sync completed.', timestamp: new Date(Date.now() - 60000).toISOString() },
    { id: 3, type: 'info', message: 'User acquisition module active.', timestamp: new Date(Date.now() - 120000).toISOString() }
];

function addFeedEntry(type, message) {
    const entry = { id: statusFeed.length + 1, type, message, timestamp: new Date().toISOString() };
    statusFeed.unshift(entry);
    if (statusFeed.length > 50) statusFeed.pop();
    return entry;
}

function getFeedData() {
    return JSON.stringify(statusFeed);
}

// Simulate live updates every 3 seconds
setInterval(() => {
    const randomMsgs = [
        { type: 'success', message: 'Health check passed.' },
        { type: 'info', message: 'Processing incoming request...' },
        { type: 'warning', message: 'High latency detected on node 4.' }
    ];
    const random = randomMsgs[Math.floor(Math.random() * randomMsgs.length)];
    addFeedEntry(random.type, random.message);
}, 3000);

console.log('Feed simulator active. Use getFeedData() to retrieve JSON.');