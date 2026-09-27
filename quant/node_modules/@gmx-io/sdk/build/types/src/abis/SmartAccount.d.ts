declare const _default: readonly [{
    readonly name: "isValidSignature";
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "_hash";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes";
        readonly name: "_signature";
        readonly type: "bytes";
    }];
    readonly outputs: readonly [{
        readonly internalType: "bytes4";
        readonly name: "magicValue";
        readonly type: "bytes4";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}];
export default _default;
