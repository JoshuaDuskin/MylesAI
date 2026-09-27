import { describe, expect, it } from "vitest";
import { buildFiltersBody } from "../indexers";
describe("buildFiltersBody", () => {
    it("should return empty object if no filters", () => {
        const input = {};
        const result = buildFiltersBody(input);
        expect(result).toEqual("{}");
    });
    it("should return correct filter string with single filter", () => {
        const input = {
            foo: "bar",
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual('{foo:"bar"}');
    });
    it("should return correct filter string with multiple filters", () => {
        const input = {
            foo: "bar",
            baz: "qux",
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual('{foo:"bar",baz:"qux"}');
    });
    it("should return correct filter string with nested filter", () => {
        const input = {
            foo: {
                bar: {
                    baz: "qux",
                },
            },
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual('{foo_:{bar_:{baz:"qux"}}}');
    });
    it("should return correct filter string with or filter", () => {
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
        const result = buildFiltersBody(input);
        expect(result).toEqual('{or:[{foo:"bar"},{baz:"qux"}]}');
    });
    it("should return correct filter string with and filter", () => {
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
        const result = buildFiltersBody(input);
        expect(result).toEqual('{and:[{foo:"bar"},{baz:"qux"}]}');
    });
    it("should strip out undefined filters", () => {
        const input = {
            foo: "bar",
            baz: undefined,
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual('{foo:"bar"}');
    });
    it("should strip out empty or", () => {
        const input = {
            or: [],
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual("{}");
    });
    it("should strip out or with empty", () => {
        const input = {
            or: [
                {},
                {
                    foo: undefined,
                },
            ],
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual("{}");
    });
    it("should throw error if or is mixed with other filters", () => {
        const input = {
            or: [
                {
                    foo: "bar",
                },
            ],
            baz: "qux",
        };
        const getResult = () => buildFiltersBody(input);
        expect(getResult).toThrowError();
    });
    it("should throw error if and is mixed with other filters", () => {
        const input = {
            and: [
                {
                    foo: "bar",
                },
            ],
            baz: "qux",
        };
        const getResult = () => buildFiltersBody(input);
        expect(getResult).toThrowError();
    });
    it("should throw not error if empty or is mixed with other filters", () => {
        const input = {
            or: [],
            baz: "qux",
        };
        const getResult = () => buildFiltersBody(input);
        expect(getResult).not.toThrowError();
    });
    it("should throw not error if empty and is mixed with other filters", () => {
        const input = {
            and: [],
            baz: "qux",
        };
        const getResult = () => buildFiltersBody(input);
        expect(getResult).not.toThrowError();
    });
    it("should format string values correctly", () => {
        const input = {
            foo: "bar",
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual('{foo:"bar"}');
    });
    it("should format number values correctly", () => {
        const input = {
            foo: 123,
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual("{foo:123}");
    });
    it("should format boolean values correctly", () => {
        const input = {
            foo: true,
            bar: false,
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual("{foo:true,bar:false}");
    });
    it("should format null values correctly", () => {
        const input = {
            foo: null,
        };
        const result = buildFiltersBody(input);
        expect(result).toEqual("{foo:null}");
    });
});
