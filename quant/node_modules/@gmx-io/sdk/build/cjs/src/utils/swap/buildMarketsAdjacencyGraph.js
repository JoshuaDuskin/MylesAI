"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.buildMarketsAdjacencyGraph = void 0;
function buildMarketsAdjacencyGraph(marketsMap) {
    const graph = {};
    for (const marketTokenAddress in marketsMap) {
        const { longTokenAddress, shortTokenAddress } = marketsMap[marketTokenAddress];
        const isSameCollaterals = longTokenAddress === shortTokenAddress;
        if (isSameCollaterals) {
            const tokenAddress = longTokenAddress;
            graph[tokenAddress] = graph[tokenAddress] || {};
            graph[tokenAddress][tokenAddress] = graph[tokenAddress][tokenAddress] || [];
            graph[tokenAddress][tokenAddress].push(marketTokenAddress);
            continue;
        }
        graph[longTokenAddress] = graph[longTokenAddress] || {};
        graph[longTokenAddress][shortTokenAddress] = graph[longTokenAddress][shortTokenAddress] || [];
        graph[longTokenAddress][shortTokenAddress].push(marketTokenAddress);
        graph[shortTokenAddress] = graph[shortTokenAddress] || {};
        graph[shortTokenAddress][longTokenAddress] = graph[shortTokenAddress][longTokenAddress] || [];
        graph[shortTokenAddress][longTokenAddress].push(marketTokenAddress);
    }
    return graph;
}
exports.buildMarketsAdjacencyGraph = buildMarketsAdjacencyGraph;
