declare const _default: readonly [{
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_admin";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_buffer";
        readonly type: "uint256";
    }, {
        readonly internalType: "address";
        readonly name: "_tokenManager";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_mintReceiver";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_glpManager";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_rewardRouter";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_maxTokenSupply";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_marginFeeBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_maxMarginFeeBasisPoints";
        readonly type: "uint256";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "constructor";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "bytes32";
        readonly name: "action";
        readonly type: "bytes32";
    }];
    readonly name: "ClearAction";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "spender";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }, {
        readonly indexed: false;
        readonly internalType: "bytes32";
        readonly name: "action";
        readonly type: "bytes32";
    }];
    readonly name: "SignalApprove";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "receiver";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }, {
        readonly indexed: false;
        readonly internalType: "bytes32";
        readonly name: "action";
        readonly type: "bytes32";
    }];
    readonly name: "SignalMint";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "bytes32";
        readonly name: "action";
        readonly type: "bytes32";
    }];
    readonly name: "SignalPendingAction";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "vault";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }];
    readonly name: "SignalRedeemUsdg";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "target";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "gov";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "bytes32";
        readonly name: "action";
        readonly type: "bytes32";
    }];
    readonly name: "SignalSetGov";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "target";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "handler";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "bool";
        readonly name: "isActive";
        readonly type: "bool";
    }, {
        readonly indexed: false;
        readonly internalType: "bytes32";
        readonly name: "action";
        readonly type: "bytes32";
    }];
    readonly name: "SignalSetHandler";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "vault";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "priceFeed";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "bytes32";
        readonly name: "action";
        readonly type: "bytes32";
    }];
    readonly name: "SignalSetPriceFeed";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "vault";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "tokenDecimals";
        readonly type: "uint256";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "tokenWeight";
        readonly type: "uint256";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "minProfitBps";
        readonly type: "uint256";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "maxUsdgAmount";
        readonly type: "uint256";
    }, {
        readonly indexed: false;
        readonly internalType: "bool";
        readonly name: "isStable";
        readonly type: "bool";
    }, {
        readonly indexed: false;
        readonly internalType: "bool";
        readonly name: "isShortable";
        readonly type: "bool";
    }];
    readonly name: "SignalVaultSetTokenConfig";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "target";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "receiver";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }, {
        readonly indexed: false;
        readonly internalType: "bytes32";
        readonly name: "action";
        readonly type: "bytes32";
    }];
    readonly name: "SignalWithdrawToken";
    readonly type: "event";
}, {
    readonly inputs: readonly [];
    readonly name: "MAX_BUFFER";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "MAX_FUNDING_RATE_FACTOR";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "MAX_LEVERAGE_VALIDATION";
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
    readonly name: "admin";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_spender";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "approve";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vester";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "_accounts";
        readonly type: "address[]";
    }, {
        readonly internalType: "uint256[]";
        readonly name: "_amounts";
        readonly type: "uint256[]";
    }];
    readonly name: "batchSetBonusRewards";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
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
    readonly name: "batchWithdrawFees";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "buffer";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "_action";
        readonly type: "bytes32";
    }];
    readonly name: "cancelAction";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }];
    readonly name: "disableLeverage";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }];
    readonly name: "enableLeverage";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "glpManager";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_referralStorage";
        readonly type: "address";
    }, {
        readonly internalType: "bytes32";
        readonly name: "_code";
        readonly type: "bytes32";
    }, {
        readonly internalType: "address";
        readonly name: "_newAccount";
        readonly type: "address";
    }];
    readonly name: "govSetCodeOwner";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "initGlpManager";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "initRewardRouter";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly name: "isHandler";
    readonly outputs: readonly [{
        readonly internalType: "bool";
        readonly name: "";
        readonly type: "bool";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly name: "isKeeper";
    readonly outputs: readonly [{
        readonly internalType: "bool";
        readonly name: "";
        readonly type: "bool";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "marginFeeBasisPoints";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "maxMarginFeeBasisPoints";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "maxTokenSupply";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "mintReceiver";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "";
        readonly type: "bytes32";
    }];
    readonly name: "pendingActions";
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
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_receiver";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "processMint";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "redeemUsdg";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_account";
        readonly type: "address";
    }];
    readonly name: "removeAdmin";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "rewardRouter";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_admin";
        readonly type: "address";
    }];
    readonly name: "setAdmin";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_buffer";
        readonly type: "uint256";
    }];
    readonly name: "setBuffer";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_handler";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_isActive";
        readonly type: "bool";
    }];
    readonly name: "setContractHandler";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_target";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_admin";
        readonly type: "address";
    }];
    readonly name: "setExternalAdmin";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_taxBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_stableTaxBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_mintBurnFeeBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_swapFeeBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_stableSwapFeeBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_marginFeeBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_liquidationFeeUsd";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_minProfitTime";
        readonly type: "uint256";
    }, {
        readonly internalType: "bool";
        readonly name: "_hasDynamicFees";
        readonly type: "bool";
    }];
    readonly name: "setFees";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_fundingInterval";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_fundingRateFactor";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_stableFundingRateFactor";
        readonly type: "uint256";
    }];
    readonly name: "setFundingRate";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_cooldownDuration";
        readonly type: "uint256";
    }];
    readonly name: "setGlpCooldownDuration";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_target";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_gov";
        readonly type: "address";
    }];
    readonly name: "setGov";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_target";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_handler";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_isActive";
        readonly type: "bool";
    }];
    readonly name: "setHandler";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_inPrivateLiquidationMode";
        readonly type: "bool";
    }];
    readonly name: "setInPrivateLiquidationMode";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_inPrivateTransferMode";
        readonly type: "bool";
    }];
    readonly name: "setInPrivateTransferMode";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_isLeverageEnabled";
        readonly type: "bool";
    }];
    readonly name: "setIsLeverageEnabled";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_isSwapEnabled";
        readonly type: "bool";
    }];
    readonly name: "setIsSwapEnabled";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_keeper";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_isActive";
        readonly type: "bool";
    }];
    readonly name: "setKeeper";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_liquidator";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_isActive";
        readonly type: "bool";
    }];
    readonly name: "setLiquidator";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_marginFeeBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_maxMarginFeeBasisPoints";
        readonly type: "uint256";
    }];
    readonly name: "setMarginFeeBasisPoints";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_maxGasPrice";
        readonly type: "uint256";
    }];
    readonly name: "setMaxGasPrice";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "setMaxGlobalShortSize";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_maxLeverage";
        readonly type: "uint256";
    }];
    readonly name: "setMaxLeverage";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_priceFeed";
        readonly type: "address";
    }];
    readonly name: "setPriceFeed";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_referralStorage";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_referrer";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_tierId";
        readonly type: "uint256";
    }];
    readonly name: "setReferrerTier";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_shortsTrackerAveragePriceWeight";
        readonly type: "uint256";
    }];
    readonly name: "setShortsTrackerAveragePriceWeight";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bool";
        readonly name: "_shouldToggleIsLeverageEnabled";
        readonly type: "bool";
    }];
    readonly name: "setShouldToggleIsLeverageEnabled";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_taxBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_stableTaxBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_mintBurnFeeBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_swapFeeBasisPoints";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_stableSwapFeeBasisPoints";
        readonly type: "uint256";
    }];
    readonly name: "setSwapFees";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_referralStorage";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_tierId";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_totalRebate";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_discountShare";
        readonly type: "uint256";
    }];
    readonly name: "setTier";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_tokenWeight";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_minProfitBps";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_maxUsdgAmount";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_bufferAmount";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_usdgAmount";
        readonly type: "uint256";
    }];
    readonly name: "setTokenConfig";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
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
    }, {
        readonly internalType: "uint256[]";
        readonly name: "_usdgAmounts";
        readonly type: "uint256[]";
    }];
    readonly name: "setUsdgAmounts";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "contract IVaultUtils";
        readonly name: "_vaultUtils";
        readonly type: "address";
    }];
    readonly name: "setVaultUtils";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "shouldToggleIsLeverageEnabled";
    readonly outputs: readonly [{
        readonly internalType: "bool";
        readonly name: "";
        readonly type: "bool";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_spender";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "signalApprove";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_receiver";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "signalMint";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "signalRedeemUsdg";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_target";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_gov";
        readonly type: "address";
    }];
    readonly name: "signalSetGov";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_target";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_handler";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_isActive";
        readonly type: "bool";
    }];
    readonly name: "signalSetHandler";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_priceFeed";
        readonly type: "address";
    }];
    readonly name: "signalSetPriceFeed";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_tokenDecimals";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_tokenWeight";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_minProfitBps";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_maxUsdgAmount";
        readonly type: "uint256";
    }, {
        readonly internalType: "bool";
        readonly name: "_isStable";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_isShortable";
        readonly type: "bool";
    }];
    readonly name: "signalVaultSetTokenConfig";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_target";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_receiver";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "signalWithdrawToken";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "tokenManager";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_sender";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "transferIn";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "usdgAmount";
        readonly type: "uint256";
    }];
    readonly name: "updateUsdgSupply";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_tokenDecimals";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_tokenWeight";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_minProfitBps";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_maxUsdgAmount";
        readonly type: "uint256";
    }, {
        readonly internalType: "bool";
        readonly name: "_isStable";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_isShortable";
        readonly type: "bool";
    }];
    readonly name: "vaultSetTokenConfig";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_vault";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_receiver";
        readonly type: "address";
    }];
    readonly name: "withdrawFees";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_target";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "_receiver";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "withdrawToken";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}];
export default _default;
