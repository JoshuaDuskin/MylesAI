"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const findReachableTokens_1 = require("../findReachableTokens");
(0, vitest_1.describe)("findReachableTokens", () => {
    (0, vitest_1.it)("should find directly reachable tokens", () => {
        const graph = {
            ETH: {
                USDC: ["ETH [ETH-USDC]"],
            },
            USDC: {
                ETH: ["ETH [ETH-USDC]"],
            },
        };
        const result = (0, findReachableTokens_1.findReachableTokens)(graph);
        (0, vitest_1.expect)(result).toEqual({
            ETH: ["ETH", "USDC"],
            USDC: ["USDC", "ETH"],
        });
    });
    (0, vitest_1.it)("should find multi-hop reachable tokens", () => {
        const graph = {
            ETH: {
                USDC: ["ETH [ETH-USDC]"],
                BTC: ["BTC [BTC-ETH]"],
            },
            USDC: {
                ETH: ["ETH [ETH-USDC]"],
                BTC: ["BTC [BTC-USDC]"],
            },
            BTC: {
                ETH: ["BTC [BTC-ETH]"],
                USDC: ["BTC [BTC-USDC]"],
            },
        };
        const result = (0, findReachableTokens_1.findReachableTokens)(graph);
        (0, vitest_1.expect)(result).toEqual({
            ETH: ["ETH", "USDC", "BTC"],
            USDC: ["USDC", "ETH", "BTC"],
            BTC: ["BTC", "ETH", "USDC"],
        });
    });
    (0, vitest_1.it)("should handle multiple markets between same tokens", () => {
        const graph = {
            ETH: {
                USDC: ["ETH [ETH-USDC]", "ETH [ETH-USDC-2]"],
            },
            USDC: {
                ETH: ["ETH [ETH-USDC]", "ETH [ETH-USDC-2]"],
            },
        };
        const result = (0, findReachableTokens_1.findReachableTokens)(graph);
        (0, vitest_1.expect)(result).toEqual({
            ETH: ["ETH", "USDC"],
            USDC: ["USDC", "ETH"],
        });
    });
    (0, vitest_1.it)("should not include self-loops", () => {
        const graph = {
            ETH: {
                ETH: ["ETH [ETH-ETH]"],
            },
        };
        const result = (0, findReachableTokens_1.findReachableTokens)(graph);
        (0, vitest_1.expect)(result).toEqual({
            ETH: ["ETH"],
        });
    });
    (0, vitest_1.it)("should handle empty graph", () => {
        const graph = {};
        const result = (0, findReachableTokens_1.findReachableTokens)(graph);
        (0, vitest_1.expect)(result).toEqual({});
    });
    (0, vitest_1.it)("should handle isolated tokens", () => {
        const graph = {
            ETH: {},
            USDC: {},
        };
        const result = (0, findReachableTokens_1.findReachableTokens)(graph);
        (0, vitest_1.expect)(result).toEqual({
            ETH: ["ETH"],
            USDC: ["USDC"],
        });
    });
    (0, vitest_1.it)("should respect MAX_EDGE_PATH_LENGTH limit", () => {
        const graph = {
            ETH: {
                USDC: ["ETH [ETH-USDC]"],
            },
            USDC: {
                ETH: ["ETH [ETH-USDC]"],
                BTC: ["BTC [BTC-USDC]"],
            },
            BTC: {
                USDC: ["BTC [BTC-USDC]"],
                WBTC: ["WBTC [WBTC-BTC]"],
            },
            WBTC: {
                BTC: ["WBTC [WBTC-BTC]"],
                USDT: ["USDT [USDT-WBTC]"],
            },
            USDT: {
                WBTC: ["USDT [USDT-WBTC]"],
                DAI: ["DAI [DAI-USDT]"],
            },
            DAI: {
                USDT: ["DAI [DAI-USDT]"],
            },
        };
        const result = (0, findReachableTokens_1.findReachableTokens)(graph);
        (0, vitest_1.expect)(result.ETH).toEqual(["ETH", "USDC", "BTC", "WBTC"]);
        (0, vitest_1.expect)(result.USDC).toEqual(["USDC", "ETH", "BTC", "WBTC", "USDT"]);
        (0, vitest_1.expect)(result.BTC).toEqual(["BTC", "USDC", "WBTC", "ETH", "USDT", "DAI"]);
        (0, vitest_1.expect)(result.WBTC).toEqual(["WBTC", "BTC", "USDT", "USDC", "DAI", "ETH"]);
        (0, vitest_1.expect)(result.USDT).toEqual(["USDT", "WBTC", "DAI", "BTC", "USDC"]);
        (0, vitest_1.expect)(result.DAI).toEqual(["DAI", "USDT", "WBTC", "BTC"]);
    });
});
