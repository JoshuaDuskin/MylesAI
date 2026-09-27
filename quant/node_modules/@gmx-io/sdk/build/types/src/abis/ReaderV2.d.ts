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
    readonly inputs: readonly [];
    readonly name: "POSITION_PROPS_LENGTH";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "PRICE_PRECISION";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "USDG_DECIMALS";
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
    readonly name: "getFeeBasisPoints";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }, {
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
        readonly internalType: "uint256";
        readonly name: "_usdgAmount";
        readonly type: "uint256";
    }, {
        readonly internalType: "address[]";
        readonly name: "_tokens";
        readonly type: "address[]";
    }];
    readonly name: "getFullVaultTokenInfo";
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
        readonly internalType: "contract IVaultPriceFeed";
        readonly name: "_priceFeed";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_tokens";
        readonly type: "address[]";
    }];
    readonly name: "getPrices";
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
        readonly internalType: "contract IERC20";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_accounts";
        readonly type: "address[]";
    }];
    readonly name: "getTotalBalance";
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
    readonly name: "getVaultTokenInfoV2";
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
    readonly name: "getVestingInfo";
    readonly outputs: readonly [{
        readonly internalType: "uint256[]";
        readonly name: "";
        readonly type: "uint256[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "gov";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "hasMaxGlobalShortSizes";
    readonly outputs: readonly [{
        readonly internalType: "bool";
        readonly name: "";
        readonly type: "bool";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bool";
        readonly name: "_hasMaxGlobalShortSizes";
        readonly type: "bool";
    }];
    readonly name: "setConfig";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_gov";
        readonly type: "address";
    }];
    readonly name: "setGov";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}];
export default _default;
