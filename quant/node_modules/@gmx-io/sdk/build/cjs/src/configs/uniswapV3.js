"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.hasUniswapV3Deployment = exports.getUniswapV3Deployment = void 0;
const chains_1 = require("./chains");
const DEPLOYMENTS = {
    [chains_1.ARBITRUM]: {
        positionManager: "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
        factory: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    },
};
function getUniswapV3Deployment(chainId) {
    return DEPLOYMENTS[chainId];
}
exports.getUniswapV3Deployment = getUniswapV3Deployment;
function hasUniswapV3Deployment(chainId) {
    return Boolean(getUniswapV3Deployment(chainId));
}
exports.hasUniswapV3Deployment = hasUniswapV3Deployment;
