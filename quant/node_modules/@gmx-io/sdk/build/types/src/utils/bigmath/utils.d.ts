export declare const bigMath: {
    abs(x: bigint): bigint;
    mulDiv(x: bigint, y: bigint, z: bigint, roundUpMagnitude?: boolean): bigint;
    max(max: bigint, ...rest: bigint[]): bigint;
    min(min: bigint, ...rest: bigint[]): bigint;
    avg(...values: (bigint | undefined)[]): bigint | undefined;
    divRound(x: bigint, y: bigint): bigint;
    divRoundUp(x: bigint, y: bigint): bigint;
    mulmod(x: bigint, y: bigint, m: bigint): bigint;
    clamp(value: bigint, min: bigint, max: bigint): bigint;
};
