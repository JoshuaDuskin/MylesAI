declare const _default: readonly [{
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }];
    readonly name: "StakeGlp";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "account";
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
    readonly name: "StakeGmx";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }];
    readonly name: "UnstakeGlp";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "account";
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
    readonly name: "UnstakeGmx";
    readonly type: "event";
}, {
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
        readonly internalType: "address";
        readonly name: "_sender";
        readonly type: "address";
    }];
    readonly name: "acceptTransfer";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address[]";
        readonly name: "_accounts";
        readonly type: "address[]";
    }];
    readonly name: "batchCompoundForAccounts";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address[]";
        readonly name: "_accounts";
        readonly type: "address[]";
    }];
    readonly name: "batchRestakeForAccounts";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address[]";
        readonly name: "_accounts";
        readonly type: "address[]";
    }, {
        readonly internalType: "uint256[]";
        readonly name: "_amounts";
        readonly type: "uint256[]";
    }];
    readonly name: "batchStakeGmxForAccounts";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "bnGmx";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "bonusGmxTracker";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "claim";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "claimEsGmx";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "claimFees";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "compound";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "esGmx";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "extendedGmxTracker";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "externalHandler";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "feeGlpTracker";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "feeGmxTracker";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "glp";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
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
    readonly inputs: readonly [];
    readonly name: "glpVester";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "gmx";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "gmxVester";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
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
    readonly name: "govToken";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bool";
        readonly name: "_shouldClaimGmx";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldStakeGmx";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldClaimEsGmx";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldStakeEsGmx";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldStakeMultiplierPoints";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldClaimWeth";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldConvertWethToEth";
        readonly type: "bool";
    }];
    readonly name: "handleRewards";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_gmxReceiver";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldClaimGmx";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldStakeGmx";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldClaimEsGmx";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldStakeEsGmx";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldStakeMultiplierPoints";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldClaimWeth";
        readonly type: "bool";
    }, {
        readonly internalType: "bool";
        readonly name: "_shouldConvertWethToEth";
        readonly type: "bool";
    }];
    readonly name: "handleRewardsV2";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "inRestakingMode";
    readonly outputs: readonly [{
        readonly internalType: "bool";
        readonly name: "";
        readonly type: "bool";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "inStrictTransferMode";
    readonly outputs: readonly [{
        readonly internalType: "bool";
        readonly name: "";
        readonly type: "bool";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly components: readonly [{
            readonly internalType: "address";
            readonly name: "weth";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "gmx";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "esGmx";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "bnGmx";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "glp";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "stakedGmxTracker";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "bonusGmxTracker";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "extendedGmxTracker";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "feeGmxTracker";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "feeGlpTracker";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "stakedGlpTracker";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "glpManager";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "gmxVester";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "glpVester";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "externalHandler";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "govToken";
            readonly type: "address";
        }];
        readonly internalType: "struct RewardRouterV2.InitializeParams";
        readonly name: "_initializeParams";
        readonly type: "tuple";
    }];
    readonly name: "initialize";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "isInitialized";
    readonly outputs: readonly [{
        readonly internalType: "bool";
        readonly name: "";
        readonly type: "bool";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
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
    readonly name: "makeExternalCalls";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "maxBoostBasisPoints";
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
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_minUsdg";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_minGlp";
        readonly type: "uint256";
    }];
    readonly name: "mintAndStakeGlp";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_minUsdg";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_minGlp";
        readonly type: "uint256";
    }];
    readonly name: "mintAndStakeGlpETH";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes[]";
        readonly name: "data";
        readonly type: "bytes[]";
    }];
    readonly name: "multicall";
    readonly outputs: readonly [{
        readonly internalType: "bytes[]";
        readonly name: "results";
        readonly type: "bytes[]";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly name: "pendingReceivers";
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
        readonly name: "_govToken";
        readonly type: "address";
    }];
    readonly name: "setGovToken";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bool";
        readonly name: "_inRestakingMode";
        readonly type: "bool";
    }];
    readonly name: "setInRestakingMode";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bool";
        readonly name: "_inStrictTransferMode";
        readonly type: "bool";
    }];
    readonly name: "setInStrictTransferMode";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_maxBoostBasisPoints";
        readonly type: "uint256";
    }];
    readonly name: "setMaxBoostBasisPoints";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "enum RewardRouterV2.VotingPowerType";
        readonly name: "_votingPowerType";
        readonly type: "uint8";
    }];
    readonly name: "setVotingPowerType";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "_receiver";
        readonly type: "address";
    }];
    readonly name: "signalTransfer";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "stakeEsGmx";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "stakeGmx";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "stakedGlpTracker";
    readonly outputs: readonly [{
        readonly internalType: "address";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "stakedGmxTracker";
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
        readonly name: "_tokenOut";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "_glpAmount";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_minOut";
        readonly type: "uint256";
    }, {
        readonly internalType: "address";
        readonly name: "_receiver";
        readonly type: "address";
    }];
    readonly name: "unstakeAndRedeemGlp";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_glpAmount";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "_minOut";
        readonly type: "uint256";
    }, {
        readonly internalType: "address payable";
        readonly name: "_receiver";
        readonly type: "address";
    }];
    readonly name: "unstakeAndRedeemGlpETH";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "unstakeEsGmx";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "_amount";
        readonly type: "uint256";
    }];
    readonly name: "unstakeGmx";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "votingPowerType";
    readonly outputs: readonly [{
        readonly internalType: "enum RewardRouterV2.VotingPowerType";
        readonly name: "";
        readonly type: "uint8";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "weth";
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
        readonly name: "_account";
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
}, {
    readonly stateMutability: "payable";
    readonly type: "receive";
}];
export default _default;
