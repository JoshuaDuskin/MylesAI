"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.estimateGlvWithdrawalOraclePriceCount = exports.estimateGlvDepositOraclePriceCount = exports.estimateShiftOraclePriceCount = exports.estimateOrderOraclePriceCount = exports.estimateWithdrawalOraclePriceCount = exports.estimateDepositOraclePriceCount = void 0;
// @see https://github.com/gmx-io/gmx-synthetics/blob/6ed9be061d8fcc0dc7bc5d34dee3bf091408a1bf/contracts/gas/GasUtils.sol#L218-L234
function estimateDepositOraclePriceCount(swapsCount) {
    return 3n + BigInt(swapsCount);
}
exports.estimateDepositOraclePriceCount = estimateDepositOraclePriceCount;
function estimateWithdrawalOraclePriceCount(swapsCount) {
    return 3n + BigInt(swapsCount);
}
exports.estimateWithdrawalOraclePriceCount = estimateWithdrawalOraclePriceCount;
function estimateOrderOraclePriceCount(swapsCount) {
    return 3n + BigInt(swapsCount);
}
exports.estimateOrderOraclePriceCount = estimateOrderOraclePriceCount;
function estimateShiftOraclePriceCount() {
    return 4n;
}
exports.estimateShiftOraclePriceCount = estimateShiftOraclePriceCount;
function estimateGlvDepositOraclePriceCount(marketCount, swapsCount = 0n) {
    return 2n + marketCount + swapsCount;
}
exports.estimateGlvDepositOraclePriceCount = estimateGlvDepositOraclePriceCount;
function estimateGlvWithdrawalOraclePriceCount(marketCount, swapsCount = 0n) {
    return 2n + marketCount + swapsCount;
}
exports.estimateGlvWithdrawalOraclePriceCount = estimateGlvWithdrawalOraclePriceCount;
