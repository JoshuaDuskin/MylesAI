export declare const MAX_REFERRAL_CODE_LENGTH = 20;
import { Hash } from "viem";
export declare function decodeReferralCode(hexCode?: Hash): string;
export declare function encodeReferralCode(code: string): `0x${string}`;
