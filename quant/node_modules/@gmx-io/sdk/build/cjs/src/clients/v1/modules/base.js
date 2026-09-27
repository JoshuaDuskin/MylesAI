"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Module = void 0;
class Module {
    constructor(sdk) {
        this.sdk = sdk;
        this.sdk = sdk;
    }
    get oracle() {
        return this.sdk.oracle;
    }
    get chainId() {
        return this.sdk.chainId;
    }
    get account() {
        return this.sdk.account;
    }
}
exports.Module = Module;
