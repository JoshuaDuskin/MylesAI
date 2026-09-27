// @see https://github.com/gmx-io/gmx-synthetics/blob/6ed9be061d8fcc0dc7bc5d34dee3bf091408a1bf/contracts/gas/GasUtils.sol#L218-L234
export function estimateDepositOraclePriceCount(swapsCount) {
    return 3n + BigInt(swapsCount);
}
export function estimateWithdrawalOraclePriceCount(swapsCount) {
    return 3n + BigInt(swapsCount);
}
export function estimateOrderOraclePriceCount(swapsCount) {
    return 3n + BigInt(swapsCount);
}
export function estimateShiftOraclePriceCount() {
    return 4n;
}
export function estimateGlvDepositOraclePriceCount(marketCount, swapsCount = 0n) {
    return 2n + marketCount + swapsCount;
}
export function estimateGlvWithdrawalOraclePriceCount(marketCount, swapsCount = 0n) {
    return 2n + marketCount + swapsCount;
}
