"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const chains_1 = require("../../configs/chains");
const tokens_1 = require("../../configs/tokens");
const numbers_1 = require("../numbers");
const executionFee_1 = require("./executionFee");
(0, vitest_1.describe)("getExecutionFee", () => {
    const chainId = chains_1.ARBITRUM;
    const gasLimits = {
        estimatedGasFeeBaseAmount: 600000n,
        estimatedGasFeePerOraclePrice: 250000n,
        estimatedFeeMultiplierFactor: 1000000000000000000000000000000n,
    };
    const tokensData = {
        "0xAddress": {
            decimals: 18,
            prices: {
                minPrice: (0, numbers_1.expandDecimals)(5, 18),
            },
        },
        [tokens_1.NATIVE_TOKEN_ADDRESS]: {
            decimals: 18,
            prices: {
                minPrice: (0, numbers_1.expandDecimals)(2, 18),
            },
        },
    };
    (0, vitest_1.it)("should return undefined if native token is not found", () => {
        const result = (0, executionFee_1.getExecutionFee)(chainId, gasLimits, {}, 0n, 0n, 0n);
        (0, vitest_1.expect)(result).toBeUndefined();
    });
    (0, vitest_1.it)("should return feeUsd for native token 1-2 price", () => {
        const result = (0, executionFee_1.getExecutionFee)(chainId, gasLimits, tokensData, 5000000n, 2750000001n, 4n);
        (0, vitest_1.expect)(result).toEqual({
            feeUsd: 36300000013200000n,
            feeTokenAmount: 18150000006600000n,
            gasLimit: 6600000n,
            feeToken: tokensData[tokens_1.NATIVE_TOKEN_ADDRESS],
            isFeeHigh: false,
            isFeeVeryHigh: false,
        });
    });
    (0, vitest_1.it)("should return isFeeHigh", () => {
        const result = (0, executionFee_1.getExecutionFee)(chainId, gasLimits, tokensData, 5000000n, (0, numbers_1.expandDecimals)(5, 23), 4n);
        (0, vitest_1.expect)(result).toEqual({
            feeUsd: 6600000000000000000000000000000n,
            gasLimit: 6600000n,
            feeTokenAmount: 3300000000000000000000000000000n,
            feeToken: tokensData[tokens_1.NATIVE_TOKEN_ADDRESS],
            isFeeHigh: true,
            isFeeVeryHigh: false,
        });
    });
    (0, vitest_1.it)("should return isFeeHigh", () => {
        const result = (0, executionFee_1.getExecutionFee)(chainId, gasLimits, tokensData, 5000000n, (0, numbers_1.expandDecimals)(1, 25), 4n);
        (0, vitest_1.expect)(result).toEqual({
            feeUsd: 132000000000000000000000000000000n,
            feeTokenAmount: 66000000000000000000000000000000n,
            gasLimit: 6600000n,
            feeToken: tokensData[tokens_1.NATIVE_TOKEN_ADDRESS],
            isFeeHigh: true,
            isFeeVeryHigh: true,
        });
    });
    (0, vitest_1.it)("should correctly calculate fee for 1 part", () => {
        const result = (0, executionFee_1.getExecutionFee)(chainId, gasLimits, tokensData, 5000000n, 10000000n, 4n, 1);
        (0, vitest_1.expect)(result).toEqual({
            feeUsd: 132000000000000n,
            feeTokenAmount: 66000000000000n,
            gasLimit: 6600000n,
            feeToken: tokensData[tokens_1.NATIVE_TOKEN_ADDRESS],
            isFeeHigh: false,
            isFeeVeryHigh: false,
        });
    });
    (0, vitest_1.it)("should correctly calculate fee for 5 parts", () => {
        const result = (0, executionFee_1.getExecutionFee)(chainId, gasLimits, tokensData, 5000000n, 10000000n, 4n, 5);
        (0, vitest_1.expect)(result).toEqual({
            feeUsd: 660000000000000n,
            feeTokenAmount: 330000000000000n,
            gasLimit: 6600000n,
            feeToken: tokensData[tokens_1.NATIVE_TOKEN_ADDRESS],
            isFeeHigh: false,
            isFeeVeryHigh: false,
        });
    });
    (0, vitest_1.it)("should correctly calculate fee for 12 parts", () => {
        const result = (0, executionFee_1.getExecutionFee)(chainId, gasLimits, tokensData, 5000000n, 10000000n, 4n, 12);
        (0, vitest_1.expect)(result).toEqual({
            feeUsd: 1584000000000000n,
            feeTokenAmount: 792000000000000n,
            gasLimit: 6600000n,
            feeToken: tokensData[tokens_1.NATIVE_TOKEN_ADDRESS],
            isFeeHigh: false,
            isFeeVeryHigh: false,
        });
    });
});
