declare const _default: readonly [{
    readonly inputs: readonly [{
        readonly internalType: "uint32[]";
        readonly name: "";
        readonly type: "uint32[]";
    }];
    readonly name: "observe";
    readonly outputs: readonly [{
        readonly internalType: "int56[]";
        readonly name: "tickCumulatives";
        readonly type: "int56[]";
    }, {
        readonly internalType: "uint160[]";
        readonly name: "secondsPerLiquidityCumulativeX128s";
        readonly type: "uint160[]";
    }];
    readonly stateMutability: "pure";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "slot0";
    readonly outputs: readonly [{
        readonly internalType: "uint160";
        readonly name: "sqrtPriceX96";
        readonly type: "uint160";
    }, {
        readonly internalType: "int24";
        readonly name: "tick";
        readonly type: "int24";
    }, {
        readonly internalType: "uint16";
        readonly name: "observationIndex";
        readonly type: "uint16";
    }, {
        readonly internalType: "uint16";
        readonly name: "observationCardinality";
        readonly type: "uint16";
    }, {
        readonly internalType: "uint16";
        readonly name: "observationCardinalityNext";
        readonly type: "uint16";
    }, {
        readonly internalType: "uint8";
        readonly name: "feeProtocol";
        readonly type: "uint8";
    }, {
        readonly internalType: "bool";
        readonly name: "unlocked";
        readonly type: "bool";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "tickSpacing";
    readonly outputs: readonly [{
        readonly internalType: "int24";
        readonly name: "";
        readonly type: "int24";
    }];
    readonly stateMutability: "pure";
    readonly type: "function";
}];
export default _default;
