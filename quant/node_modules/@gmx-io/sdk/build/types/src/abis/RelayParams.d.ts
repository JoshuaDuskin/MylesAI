declare const _default: readonly [{
    readonly components: readonly [{
        readonly internalType: "address[]";
        readonly name: "tokens";
        readonly type: "address[]";
    }, {
        readonly internalType: "address[]";
        readonly name: "providers";
        readonly type: "address[]";
    }, {
        readonly internalType: "bytes[]";
        readonly name: "data";
        readonly type: "bytes[]";
    }];
    readonly internalType: "struct OracleUtils.SetPricesParams";
    readonly name: "oracleParams";
    readonly type: "tuple";
}, {
    readonly components: readonly [{
        readonly internalType: "address[]";
        readonly name: "sendTokens";
        readonly type: "address[]";
    }, {
        readonly internalType: "uint256[]";
        readonly name: "sendAmounts";
        readonly type: "uint256[]";
    }, {
        readonly internalType: "address[]";
        readonly name: "externalCallTargets";
        readonly type: "address[]";
    }, {
        readonly internalType: "bytes[]";
        readonly name: "externalCallDataList";
        readonly type: "bytes[]";
    }, {
        readonly internalType: "address[]";
        readonly name: "refundTokens";
        readonly type: "address[]";
    }, {
        readonly internalType: "address[]";
        readonly name: "refundReceivers";
        readonly type: "address[]";
    }];
    readonly internalType: "struct ExternalCalls";
    readonly name: "externalCalls";
    readonly type: "tuple";
}, {
    readonly components: readonly [{
        readonly internalType: "address";
        readonly name: "owner";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "spender";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "value";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "deadline";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint8";
        readonly name: "v";
        readonly type: "uint8";
    }, {
        readonly internalType: "bytes32";
        readonly name: "r";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes32";
        readonly name: "s";
        readonly type: "bytes32";
    }, {
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }];
    readonly internalType: "struct TokenPermit[]";
    readonly name: "tokenPermits";
    readonly type: "tuple[]";
}, {
    readonly components: readonly [{
        readonly internalType: "address";
        readonly name: "feeToken";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "feeAmount";
        readonly type: "uint256";
    }, {
        readonly internalType: "address[]";
        readonly name: "feeSwapPath";
        readonly type: "address[]";
    }];
    readonly internalType: "struct FeeParams";
    readonly name: "fee";
    readonly type: "tuple";
}, {
    readonly internalType: "uint256";
    readonly name: "userNonce";
    readonly type: "uint256";
}, {
    readonly internalType: "uint256";
    readonly name: "deadline";
    readonly type: "uint256";
}, {
    readonly internalType: "uint256";
    readonly name: "desChainId";
    readonly type: "uint256";
}];
export default _default;
