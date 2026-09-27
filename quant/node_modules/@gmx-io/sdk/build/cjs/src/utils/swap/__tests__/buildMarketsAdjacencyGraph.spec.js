"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const buildMarketsAdjacencyGraph_1 = require("../buildMarketsAdjacencyGraph");
(0, vitest_1.describe)("buildMarketsAdjacencyGraph", () => {
    (0, vitest_1.it)("should build graph for single market", () => {
        const marketsMap = {
            "ETH [ETH-USDC]": {
                marketTokenAddress: "ETH [ETH-USDC]",
                indexTokenAddress: "ETH",
                longTokenAddress: "ETH",
                shortTokenAddress: "USDC",
            },
        };
        const result = (0, buildMarketsAdjacencyGraph_1.buildMarketsAdjacencyGraph)(marketsMap);
        (0, vitest_1.expect)(result).toEqual({
            ETH: {
                USDC: ["ETH [ETH-USDC]"],
            },
            USDC: {
                ETH: ["ETH [ETH-USDC]"],
            },
        });
    });
    (0, vitest_1.it)("should build graph for multiple markets", () => {
        const marketsMap = {
            "ETH [ETH-USDC]": {
                marketTokenAddress: "ETH [ETH-USDC]",
                indexTokenAddress: "ETH",
                longTokenAddress: "ETH",
                shortTokenAddress: "USDC",
            },
            "BTC [BTC-USDC]": {
                marketTokenAddress: "BTC [BTC-USDC]",
                indexTokenAddress: "BTC",
                longTokenAddress: "BTC",
                shortTokenAddress: "USDC",
            },
            "BTC [BTC-ETH]": {
                marketTokenAddress: "BTC [BTC-ETH]",
                indexTokenAddress: "BTC",
                longTokenAddress: "BTC",
                shortTokenAddress: "ETH",
            },
        };
        const result = (0, buildMarketsAdjacencyGraph_1.buildMarketsAdjacencyGraph)(marketsMap);
        (0, vitest_1.expect)(result).toEqual({
            ETH: {
                USDC: ["ETH [ETH-USDC]"],
                BTC: ["BTC [BTC-ETH]"],
            },
            USDC: {
                ETH: ["ETH [ETH-USDC]"],
                BTC: ["BTC [BTC-USDC]"],
            },
            BTC: {
                USDC: ["BTC [BTC-USDC]"],
                ETH: ["BTC [BTC-ETH]"],
            },
        });
    });
    (0, vitest_1.it)("should handle multiple markets between same tokens", () => {
        const marketsMap = {
            "ETH [ETH-USDC]": {
                marketTokenAddress: "ETH [ETH-USDC]",
                indexTokenAddress: "ETH",
                longTokenAddress: "ETH",
                shortTokenAddress: "USDC",
            },
            "ETH [ETH-USDC-2]": {
                marketTokenAddress: "ETH [ETH-USDC-2]",
                indexTokenAddress: "ETH",
                longTokenAddress: "ETH",
                shortTokenAddress: "USDC",
            },
        };
        const result = (0, buildMarketsAdjacencyGraph_1.buildMarketsAdjacencyGraph)(marketsMap);
        (0, vitest_1.expect)(result).toEqual({
            ETH: {
                USDC: ["ETH [ETH-USDC]", "ETH [ETH-USDC-2]"],
            },
            USDC: {
                ETH: ["ETH [ETH-USDC]", "ETH [ETH-USDC-2]"],
            },
        });
    });
    (0, vitest_1.it)("should skip markets with same collateral tokens", () => {
        const marketsMap = {
            "ETH [ETH-ETH]": {
                marketTokenAddress: "ETH [ETH-ETH]",
                indexTokenAddress: "ETH",
                longTokenAddress: "ETH",
                shortTokenAddress: "ETH",
            },
            "ETH [ETH-USDC]": {
                marketTokenAddress: "ETH [ETH-USDC]",
                indexTokenAddress: "ETH",
                longTokenAddress: "ETH",
                shortTokenAddress: "USDC",
            },
        };
        const result = (0, buildMarketsAdjacencyGraph_1.buildMarketsAdjacencyGraph)(marketsMap);
        (0, vitest_1.expect)(result).toEqual({
            ETH: {
                ETH: ["ETH [ETH-ETH]"],
                USDC: ["ETH [ETH-USDC]"],
            },
            USDC: {
                ETH: ["ETH [ETH-USDC]"],
            },
        });
    });
    (0, vitest_1.it)("should handle empty markets map", () => {
        const marketsMap = {};
        const result = (0, buildMarketsAdjacencyGraph_1.buildMarketsAdjacencyGraph)(marketsMap);
        (0, vitest_1.expect)(result).toEqual({});
    });
});
