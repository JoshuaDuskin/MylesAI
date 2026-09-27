"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.buildUrl = void 0;
const query_string_1 = __importDefault(require("query-string"));
function buildUrl(baseUrl, path, query) {
    const qs = query ? `?${query_string_1.default.stringify(query)}` : "";
    baseUrl = baseUrl.replace(/\/$/, "");
    return `${baseUrl}${path}${qs}`;
}
exports.buildUrl = buildUrl;
