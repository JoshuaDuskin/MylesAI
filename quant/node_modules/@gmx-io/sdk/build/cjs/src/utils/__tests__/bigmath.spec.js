"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const bigmath_1 = require("../bigmath");
(0, vitest_1.describe)("bigMath", () => {
    (0, vitest_1.describe)("abs", () => {
        (0, vitest_1.it)("should return the absolute value of a number", () => {
            (0, vitest_1.expect)(bigmath_1.bigMath.abs(10n)).toBe(10n);
            (0, vitest_1.expect)(bigmath_1.bigMath.abs(-10n)).toBe(10n);
        });
    });
    (0, vitest_1.describe)("mulDiv", () => {
        (0, vitest_1.it)("should return the result of multiplying two numbers and dividing by a third", () => {
            (0, vitest_1.expect)(bigmath_1.bigMath.mulDiv(10n, 10n, 2n)).toBe(50n);
            (0, vitest_1.expect)(bigmath_1.bigMath.mulDiv(10n, 10n, 3n)).toBe(33n);
        });
    });
    (0, vitest_1.describe)("max", () => {
        (0, vitest_1.it)("should return the maximum value of a list of numbers", () => {
            (0, vitest_1.expect)(bigmath_1.bigMath.max(10n, 20n, -30n)).toBe(20n);
            (0, vitest_1.expect)(bigmath_1.bigMath.max(30n, 20n, 10n)).toBe(30n);
        });
    });
    (0, vitest_1.describe)("min", () => {
        (0, vitest_1.it)("should return the minimum value of a list of numbers", () => {
            (0, vitest_1.expect)(bigmath_1.bigMath.min(10n, 20n, -30n)).toBe(-30n);
            (0, vitest_1.expect)(bigmath_1.bigMath.min(30n, 20n, 10n)).toBe(10n);
        });
    });
    (0, vitest_1.describe)("avg", () => {
        (0, vitest_1.it)("should return the average value of a list of numbers", () => {
            (0, vitest_1.expect)(bigmath_1.bigMath.avg(10n, 20n, 30n)).toBe(20n);
            (0, vitest_1.expect)(bigmath_1.bigMath.avg(10n, 20n, 30n, 40n, undefined)).toBe(25n);
        });
        (0, vitest_1.it)("should return undefined if no values are provided", () => {
            (0, vitest_1.expect)(bigmath_1.bigMath.avg()).toBe(undefined);
            (0, vitest_1.expect)(bigmath_1.bigMath.avg(undefined, undefined)).toBe(undefined);
        });
    });
});
