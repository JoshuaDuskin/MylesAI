"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const viem_1 = require("viem");
const vitest_1 = require("vitest");
const referrals_1 = require("../referrals");
(0, vitest_1.describe)("utils/referrals", () => {
    (0, vitest_1.it)("decode(encode(x)) === x", () => {
        const code = "test";
        const encoded = (0, referrals_1.encodeReferralCode)(code);
        const decoded = (0, referrals_1.decodeReferralCode)(encoded);
        (0, vitest_1.expect)(decoded).toEqual(code);
    });
    (0, vitest_1.it)("decodeReferralCode defaults", () => {
        (0, vitest_1.expect)((0, referrals_1.decodeReferralCode)()).toEqual("");
        (0, vitest_1.expect)((0, referrals_1.decodeReferralCode)(viem_1.zeroHash)).toEqual("");
    });
    (0, vitest_1.it)("encodeReferralCode defaults", () => {
        (0, vitest_1.expect)((0, referrals_1.encodeReferralCode)(new Array(referrals_1.MAX_REFERRAL_CODE_LENGTH + 1).fill("0").join(""))).toEqual(viem_1.zeroHash);
    });
});
