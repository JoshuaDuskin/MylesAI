"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DEFAULT_ALLOWED_SWAP_SLIPPAGE_BPS = exports.HIGH_ALLOWED_SWAP_SLIPPAGE_BPS = exports.DEFAULT_ACCEPTABLE_PRICE_IMPACT_BUFFER = exports.HIGH_SWAP_IMPACT_BPS = exports.HIGH_COLLATERAL_IMPACT_BPS = exports.HIGH_PRICE_IMPACT_BPS = exports.BASIS_POINTS_DECIMALS = exports.BASIS_POINTS_DIVISOR_BIGINT = exports.BASIS_POINTS_DIVISOR = exports.USD_DECIMALS = void 0;
var numbers_1 = require("../utils/numbers");
Object.defineProperty(exports, "USD_DECIMALS", { enumerable: true, get: function () { return numbers_1.USD_DECIMALS; } });
Object.defineProperty(exports, "BASIS_POINTS_DIVISOR", { enumerable: true, get: function () { return numbers_1.BASIS_POINTS_DIVISOR; } });
Object.defineProperty(exports, "BASIS_POINTS_DIVISOR_BIGINT", { enumerable: true, get: function () { return numbers_1.BASIS_POINTS_DIVISOR_BIGINT; } });
Object.defineProperty(exports, "BASIS_POINTS_DECIMALS", { enumerable: true, get: function () { return numbers_1.BASIS_POINTS_DECIMALS; } });
// V2
exports.HIGH_PRICE_IMPACT_BPS = 80; // 0.8%
exports.HIGH_COLLATERAL_IMPACT_BPS = 2500; // 25%
exports.HIGH_SWAP_IMPACT_BPS = 50; // 0.5%
exports.DEFAULT_ACCEPTABLE_PRICE_IMPACT_BUFFER = 30; // 0.3%
exports.HIGH_ALLOWED_SWAP_SLIPPAGE_BPS = 20; // 0.2%
exports.DEFAULT_ALLOWED_SWAP_SLIPPAGE_BPS = 100n; // 1%
