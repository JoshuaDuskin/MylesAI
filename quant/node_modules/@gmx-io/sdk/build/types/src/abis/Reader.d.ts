declare const _default: readonly [{
    readonly inputs: readonly [];
    readonly name: "BASIS_POINTS_DIVISOR";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract IVault";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_tokenIn";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_tokenOut";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amountIn";
        readonly type: "uint256";
    }];
    readonly name: "getAmountOut";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_tokens";
        readonly type: "address[]";
    }];
    readonly name: "getFees";
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
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_weth";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_tokens";
        readonly type: "address[]";
    }];
    readonly name: "getFundingRates";
    readonly outputs: readonly [{
        readonly internalType: "uint256[]";
        readonly name: "";
        readonly type: "uint256[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract IVault";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_tokenIn";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_tokenOut";
        readonly type: "address";
    }];
    readonly name: "getMaxAmountIn";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_factory";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_tokens";
        readonly type: "address[]";
    }];
    readonly name: "getPairInfo";
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
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_account";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_collateralTokens";
        readonly type: "address[]";
    }, {
        readonly internalType: "address[]";
        readonly name: "_indexTokens";
        readonly type: "address[]";
    }, {
        readonly internalType: "bool[]";
        readonly name: "_isLong";
        readonly type: "bool[]";
    }];
    readonly name: "getPositions";
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
        readonly name: "_yieldTrackers";
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
        readonly name: "_tokens";
        readonly type: "address[]";
    }];
    readonly name: "getTokenBalances";
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
        readonly name: "_tokens";
        readonly type: "address[]";
    }];
    readonly name: "getTokenBalancesWithSupplies";
    readonly outputs: readonly [{
        readonly internalType: "uint256[]";
        readonly name: "";
        readonly type: "uint256[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract IERC20";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_excludedAccounts";
        readonly type: "address[]";
    }];
    readonly name: "getTokenSupply";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address[]";
        readonly name: "_yieldTokens";
        readonly type: "address[]";
    }];
    readonly name: "getTotalStaked";
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
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_weth";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_usdgAmount";
        readonly type: "uint256";
    }, {
        readonly internalType: "address[]";
        readonly name: "_tokens";
        readonly type: "address[]";
    }];
    readonly name: "getVaultTokenInfo";
    readonly outputs: readonly [{
        readonly internalType: "uint256[]";
        readonly name: "";
        readonly type: "uint256[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}];
export default _default;
