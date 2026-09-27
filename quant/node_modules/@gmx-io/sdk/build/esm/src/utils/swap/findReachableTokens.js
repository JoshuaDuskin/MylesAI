import { objectKeysDeep } from "../objects";
import { MAX_EDGE_PATH_LENGTH } from "./constants";
export function findReachableTokens(graph) {
    const reachableTokens = {};
    const allTokens = objectKeysDeep(graph, 1).sort();
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
            if (pathLength >= MAX_EDGE_PATH_LENGTH) {
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
