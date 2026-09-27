export function getNaiveEstimatedGasBySwapCount(singleSwap, swapsCount) {
    const swapsCountBigint = BigInt(swapsCount);
    return singleSwap * swapsCountBigint;
}
