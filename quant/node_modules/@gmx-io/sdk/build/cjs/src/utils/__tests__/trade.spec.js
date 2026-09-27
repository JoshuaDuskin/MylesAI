"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const trade_1 = require("../trade");
(0, vitest_1.describe)("applySlippageToPrice", () => {
    (0, vitest_1.it)("applies positive slippage if getShouldUseMaxPrice is true", () => {
        // isIncrease=true and isLong=true => getShouldUseMaxPrice => true
        const allowedSlippage = 100; // 1%
        const price = 1000n;
        const result = (0, trade_1.applySlippageToPrice)(allowedSlippage, price, true, true);
        // expected: price * (10000+100)/10000 = 1000n * 10100n / 10000n = 1010n
        (0, vitest_1.expect)(result).toBe(1010n);
    });
    (0, vitest_1.it)("applies negative slippage if getShouldUseMaxPrice is false", () => {
        // isIncrease=true or isLong=false => getShouldUseMaxPrice => false
        const allowedSlippage = 100; // 1%
        const price = 1000n;
        const result = (0, trade_1.applySlippageToPrice)(allowedSlippage, price, true, false);
        // expected: price * (10000-100)/10000 = 1000n * 9900n / 10000n = 990n
        (0, vitest_1.expect)(result).toBe(990n);
    });
});
(0, vitest_1.describe)("applySlippageToMinOut", () => {
    (0, vitest_1.it)("reduces minOutputAmount by allowed slippage", () => {
        const allowedSlippage = 100; // 1%
        const minOutputAmount = 10000n;
        const result = (0, trade_1.applySlippageToMinOut)(allowedSlippage, minOutputAmount);
        // expected: minOut * (10000 - 100) / 10000 = 10_000n * 9900n / 10000n = 9900n
        (0, vitest_1.expect)(result).toBe(9900n);
    });
    (0, vitest_1.it)("does nothing if slippage is zero", () => {
        const allowedSlippage = 0;
        const minOutputAmount = 10000n;
        const result = (0, trade_1.applySlippageToMinOut)(allowedSlippage, minOutputAmount);
        // expected: 10_000n * (10000 - 0) / 10000n = 10_000n
        (0, vitest_1.expect)(result).toBe(10000n);
    });
});
