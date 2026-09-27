"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.findReachableTokens = void 0;
const objects_1 = require("../objects");
const constants_1 = require("./constants");
function findReachableTokens(graph) {
    const reachableTokens = {};
    const allTokens = (0, objects_1.objectKeysDeep)(graph, 1).sort();
    for (const startToken of allTokens) {
        const searchQueue = [
            {
                currentToken: startToken,
                pathLength: 0,
            },
        ];
        const visitedTokens = new Set();
        while (searchQueue.length > 0) {
            const { currentToken, pathLength } = searchQueue.shift();
            if (visitedTokens.has(currentToken)) {
                continue;
            }
            visitedTokens.add(currentToken);
            if (pathLength >= constants_1.MAX_EDGE_PATH_LENGTH) {
                continue;
            }
            for (const nextToken in graph[currentToken]) {
                searchQueue.push({
                    currentToken: nextToken,
                    pathLength: pathLength + 1,
                });
            }
        }
        reachableTokens[startToken] = Array.from(visitedTokens);
    }
    return reachableTokens;
}
exports.findReachableTokens = findReachableTokens;
