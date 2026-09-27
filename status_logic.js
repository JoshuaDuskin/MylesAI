async function getMylesStatus() {
    const config = window.mylesConfig || {};
    
    // Priority 1: Check if a public URL is configured
    if (config.RAW_STATUS_URL && config.RAW_STATUS_URL.startsWith('http')) {
        try {
            console.log(`Fetching status from public source: ${config.RAW_STATUS_URL}`);
            const response = await fetch(config.RAW_STATUS_URL);
            if (!response.ok) throw new Error("Network response was not ok");
            return await response.json();
        } catch (error) {
            console.warn("Failed to fetch from public URL:", error.message);
        }
    }

    // Priority 2: Fallback for local environment without external server
    // Since browsers cannot directly read C:\Users\... without a local server,
    // we will attempt to read from a local proxy endpoint if available, 
    // otherwise return a default 'offline' state with instructions.
    
    const localStatusUrl = config.LOCAL_STATUS_URL || '/api/status';
    
    try {
        // Attempt fetch against local relative path (requires local server)
        const response = await fetch(localStatusUrl);
        if (response.ok) return await response.json();
    } catch (e) {
        console.log("Local proxy not available or failed.");
    }

    // Default fallback: Return a structured object indicating the system is 
    // running locally but status feed is unavailable without a server.
    return {
        status: 'offline',
        message: 'Status feed requires a local HTTP server. Please run `python -m http.server` in this directory.',
        version: '1.0.0-local',
        cycle: null
    };
}

// Expose function globally for the HTML file to call
window.getMylesStatus = getMylesStatus;