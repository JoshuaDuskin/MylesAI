"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getNaiveEstimatedGasBySwapCount = void 0;
function getNaiveEstimatedGasBySwapCount(singleSwap, swapsCount) {
    const swapsCountBigint = BigInt(swapsCount);
    return singleSwap * swapsCountBigint;
}
exports.getNaiveEstimatedGasBySwapCount = getNaiveEstimatedGasBySwapCount;
