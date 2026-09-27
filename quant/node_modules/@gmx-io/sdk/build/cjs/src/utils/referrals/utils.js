"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.encodeReferralCode = exports.decodeReferralCode = exports.MAX_REFERRAL_CODE_LENGTH = void 0;
exports.MAX_REFERRAL_CODE_LENGTH = 20;
const viem_1 = require("viem");
const utils_1 = require("viem/utils");
function decodeReferralCode(hexCode) {
    if (!hexCode || hexCode === viem_1.zeroHash) {
        return "";
    }
    try {
        const bytes = (0, utils_1.hexToBytes)(hexCode);
        if (bytes.length !== 32)
            throw new Error();
        return (0, utils_1.bytesToString)(bytes).replace(/\0+$/, "");
    }
    catch (ex) {
        let code = "";
        const cleaned = hexCode.substring(2);
        for (let i = 0; i < 32; i++) {
            code += String.fromCharCode(parseInt(cleaned.substring(i * 2, i * 2 + 2), 16));
        }
        return code.trim();
    }
}
exports.decodeReferralCode = decodeReferralCode;
function encodeReferralCode(code) {
    let final = code.replace(/[^\w_]/g, ""); // replace everything other than numbers, string  and underscor to ''
    if (final.length > exports.MAX_REFERRAL_CODE_LENGTH) {
        return viem_1.zeroHash;
    }
    return (0, viem_1.padHex)((0, viem_1.stringToHex)(final), { size: 32, dir: "right" });
}
exports.encodeReferralCode = encodeReferralCode;
