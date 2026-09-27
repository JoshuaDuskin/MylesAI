declare const _default: readonly [{
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_account";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_depositTokens";
        readonly type: "address[]";
    }, {
        readonly internalType: "address[]";
        readonly name: "_rewardTrackers";
        readonly type: "address[]";
    }];
    readonly name: "getDepositBalances";
    readonly outputs: readonly [{
        readonly internalType: "uint256[]";
        readonly name: "";
        readonly type: "uint256[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_account";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_rewardTrackers";
        readonly type: "address[]";
    }];
    readonly name: "getStakingInfo";
    readonly outputs: readonly [{
        readonly internalType: "uint256[]";
        readonly name: "";
        readonly type: "uint256[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_account";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_vesters";
        readonly type: "address[]";
    }];
    readonly name: "getVestingInfoV2";
    readonly outputs: readonly [{
        readonly internalType: "uint256[]";
        readonly name: "";
        readonly type: "uint256[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}];
export default _default;
