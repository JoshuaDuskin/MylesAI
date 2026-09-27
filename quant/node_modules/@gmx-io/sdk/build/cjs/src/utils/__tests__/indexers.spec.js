"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const indexers_1 = require("../indexers");
(0, vitest_1.describe)("buildFiltersBody", () => {
    (0, vitest_1.it)("should return empty object if no filters", () => {
        const input = {};
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual("{}");
    });
    (0, vitest_1.it)("should return correct filter string with single filter", () => {
        const input = {
            foo: "bar",
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual('{foo:"bar"}');
    });
    (0, vitest_1.it)("should return correct filter string with multiple filters", () => {
        const input = {
            foo: "bar",
            baz: "qux",
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual('{foo:"bar",baz:"qux"}');
    });
    (0, vitest_1.it)("should return correct filter string with nested filter", () => {
        const input = {
            foo: {
                bar: {
                    baz: "qux",
                },
            },
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual('{foo_:{bar_:{baz:"qux"}}}');
    });
    (0, vitest_1.it)("should return correct filter string with or filter", () => {
        const input = {
            or: [
                {
                    foo: "bar",
                },
                {
                    baz: "qux",
                },
            ],
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual('{or:[{foo:"bar"},{baz:"qux"}]}');
    });
    (0, vitest_1.it)("should return correct filter string with and filter", () => {
        const input = {
            and: [
                {
                    foo: "bar",
                },
                {
                    baz: "qux",
                },
            ],
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual('{and:[{foo:"bar"},{baz:"qux"}]}');
    });
    (0, vitest_1.it)("should strip out undefined filters", () => {
        const input = {
            foo: "bar",
            baz: undefined,
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual('{foo:"bar"}');
    });
    (0, vitest_1.it)("should strip out empty or", () => {
        const input = {
            or: [],
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual("{}");
    });
    (0, vitest_1.it)("should strip out or with empty", () => {
        const input = {
            or: [
                {},
                {
                    foo: undefined,
                },
            ],
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual("{}");
    });
    (0, vitest_1.it)("should throw error if or is mixed with other filters", () => {
        const input = {
            or: [
                {
                    foo: "bar",
                },
            ],
            baz: "qux",
        };
        const getResult = () => (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(getResult).toThrowError();
    });
    (0, vitest_1.it)("should throw error if and is mixed with other filters", () => {
        const input = {
            and: [
                {
                    foo: "bar",
                },
            ],
            baz: "qux",
        };
        const getResult = () => (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(getResult).toThrowError();
    });
    (0, vitest_1.it)("should throw not error if empty or is mixed with other filters", () => {
        const input = {
            or: [],
            baz: "qux",
        };
        const getResult = () => (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(getResult).not.toThrowError();
    });
    (0, vitest_1.it)("should throw not error if empty and is mixed with other filters", () => {
        const input = {
            and: [],
            baz: "qux",
        };
        const getResult = () => (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(getResult).not.toThrowError();
    });
    (0, vitest_1.it)("should format string values correctly", () => {
        const input = {
            foo: "bar",
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual('{foo:"bar"}');
    });
    (0, vitest_1.it)("should format number values correctly", () => {
        const input = {
            foo: 123,
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual("{foo:123}");
    });
    (0, vitest_1.it)("should format boolean values correctly", () => {
        const input = {
            foo: true,
            bar: false,
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual("{foo:true,bar:false}");
    });
    (0, vitest_1.it)("should format null values correctly", () => {
        const input = {
            foo: null,
        };
        const result = (0, indexers_1.buildFiltersBody)(input);
        (0, vitest_1.expect)(result).toEqual("{foo:null}");
    });
});
