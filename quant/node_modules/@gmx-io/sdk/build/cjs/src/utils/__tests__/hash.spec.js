"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const hash_1 = require("../hash");
const LruCache_1 = require("../LruCache");
(0, vitest_1.describe)("hashData", () => {
    (0, vitest_1.it)("returns a valid hash and caches it", () => {
        const inputTypes = ["uint256", "string"];
        const inputValues = [123n, "hello"];
        const result = (0, hash_1.hashData)(inputTypes, inputValues);
        (0, vitest_1.expect)(result).toBe("0x18a25ed45d79546dfca2565caa2ee3102fb46159dea4fde1d0a9c0cc78ce94e3");
        // Check cache
        const key = JSON.stringify({ dataTypes: inputTypes, dataValues: ["123", "hello"] });
        (0, vitest_1.expect)(new LruCache_1.LRUCache(10000).has(key)).toBe(false);
    });
    (0, vitest_1.it)("returns cached hash if already computed", () => {
        const inputTypes = ["bool"];
        const inputValues = [true];
        const result1 = (0, hash_1.hashData)(inputTypes, inputValues);
        const result2 = (0, hash_1.hashData)(inputTypes, inputValues);
        (0, vitest_1.expect)(result1).toBe(result2);
    });
});
(0, vitest_1.describe)("hashString", () => {
    (0, vitest_1.it)("returns a valid hash for a string and caches it", () => {
        const str = "test-string";
        const hash1 = (0, hash_1.hashString)(str);
        const hash2 = (0, hash_1.hashString)(str);
        (0, vitest_1.expect)(hash1).toBe(hash2);
    });
});
(0, vitest_1.describe)("hashDataMap", () => {
    (0, vitest_1.it)("returns hashes for a given record map", () => {
        const result = (0, hash_1.hashDataMap)({
            first: [["string"], ["hello"]],
            second: [["uint256"], [42n]],
            empty: undefined,
        });
        (0, vitest_1.expect)(Object.keys(result)).toContain("first");
        (0, vitest_1.expect)(Object.keys(result)).toContain("second");
        (0, vitest_1.expect)(Object.keys(result)).not.toContain("empty");
    });
});
