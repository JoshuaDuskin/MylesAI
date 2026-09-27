"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TOKEN_SWAP_PATHS = exports.REACHABLE_TOKENS = exports.MARKETS_ADJACENCY_GRAPH = void 0;
const markets_1 = require("../../configs/markets");
const buildMarketsAdjacencyGraph_1 = require("./buildMarketsAdjacencyGraph");
const findReachableTokens_1 = require("./findReachableTokens");
const findSwapPathsBetweenTokens_1 = require("./findSwapPathsBetweenTokens");
const MARKETS_ADJACENCY_GRAPH = {};
exports.MARKETS_ADJACENCY_GRAPH = MARKETS_ADJACENCY_GRAPH;
for (const chainId in markets_1.MARKETS) {
    const markets = markets_1.MARKETS[chainId];
    const chainGraph = (0, buildMarketsAdjacencyGraph_1.buildMarketsAdjacencyGraph)(markets);
    MARKETS_ADJACENCY_GRAPH[chainId] = chainGraph;
}
const TOKEN_SWAP_PATHS = {};
exports.TOKEN_SWAP_PATHS = TOKEN_SWAP_PATHS;
for (const chainId in markets_1.MARKETS) {
    const chainGraph = MARKETS_ADJACENCY_GRAPH[chainId];
    const chainSwapPaths = (0, findSwapPathsBetweenTokens_1.findSwapPathsBetweenTokens)(chainGraph);
    TOKEN_SWAP_PATHS[chainId] = chainSwapPaths;
}
const REACHABLE_TOKENS = {};
exports.REACHABLE_TOKENS = REACHABLE_TOKENS;
for (const chainId in markets_1.MARKETS) {
    const chainGraph = MARKETS_ADJACENCY_GRAPH[chainId];
    const chainReachableTokens = (0, findReachableTokens_1.findReachableTokens)(chainGraph);
    REACHABLE_TOKENS[chainId] = chainReachableTokens;
}
