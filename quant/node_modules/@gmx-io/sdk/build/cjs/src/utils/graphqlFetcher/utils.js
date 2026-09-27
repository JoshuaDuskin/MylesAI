"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const cross_fetch_1 = __importDefault(require("cross-fetch"));
async function graphqlFetcher(endpoint, query, variables) {
    try {
        const response = await (0, cross_fetch_1.default)(endpoint, {
            body: JSON.stringify({ query, variables }),
            headers: { "Content-type": "application/json" },
            method: "POST",
        });
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        const { data } = await response.json();
        return data;
    }
    catch (error) {
        throw new Error(`Error fetching GraphQL query: ${error}`);
    }
}
exports.default = graphqlFetcher;
