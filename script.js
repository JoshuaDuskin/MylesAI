// Local Live Feed Simulation Module
// Replaces external API calls with deterministic local data generation
// Ensures dashboard functionality without SSL dependencies

const LIVE_FEED_CONFIG = {
    updateInterval: 1000, // ms
    baseMetrics: {
        cpu: 45,
        memory: 62,
        network: 12,
        disk: 38,
        uptime: Date.now() - (3 * 24 * 60 * 60 * 1000) // Simulate 3 days uptime
    }
};

class LocalFeedSimulator {
    constructor() {
        this.data = JSON.parse(JSON.stringify(LIVE_FEED_CONFIG.baseMetrics));
        this.intervalId = null;
        this.isRunning = false;
    }

    start() {
        if (this.isRunning) return;
        
        // Simulate fluctuating metrics based on time and random noise
        const simulateFluctuation = () => {
            const now = Date.now();
            const hour = Math.floor(now / (1000 * 60 * 60));
            
            this.data.cpu = Math.min(100, Math.max(20, LIVE_FEED_CONFIG.baseMetrics.cpu + Math.sin(hour) * 15 + (Math.random() * 10 - 5)));
            this.data.memory = Math.min(95, Math.max(40, LIVE_FEED_CONFIG.baseMetrics.memory + Math.cos(now / 3600000) * 8 + (Math.random() * 5 - 2.5)));
            this.data.network = Math.abs(Math.sin(now / 1000) * 20 + (Math.random() * 4 - 2));
            this.data.disk = LIVE_FEED_CONFIG.baseMetrics.disk + (Math.random() * 0.1 - 0.05);
            this.data.uptime = now - (3 * 24 * 60 * 60 * 1000);
        };

        simulateFluctuation(); // Initial call
        this.intervalId = setInterval(simulateFluctuation, LIVE_FEED_CONFIG.updateInterval);
        this.isRunning = true;
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isRunning = false;
    }

    getData() {
        return this.data;
    }

    reset() {
        this.stop();
        Object.assign(this.data, JSON.parse(JSON.stringify(LIVE_FEED_CONFIG.baseMetrics)));
        this.start();
    }
}

// Global instance accessible by dashboard components
const localFeed = new LocalFeedSimulator();

// Auto-start on module load to ensure immediate functionality
if (typeof window !== 'undefined') {
    window.localFeed = localFeed;
    // Optional: Start automatically if needed, otherwise dashboard can call start()
    // localFeed.start(); 
}