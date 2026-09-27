declare const _default: readonly [{
    readonly inputs: readonly [{
        readonly internalType: "contract Router";
        readonly name: "_router";
        readonly type: "address";
    }, {
        readonly internalType: "contract RoleStore";
        readonly name: "_roleStore";
        readonly type: "address";
    }, {
        readonly internalType: "contract DataStore";
        readonly name: "_dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "contract EventEmitter";
        readonly name: "_eventEmitter";
        readonly type: "address";
    }, {
        readonly internalType: "contract IGlvDepositHandler";
        readonly name: "_glvDepositHandler";
        readonly type: "address";
    }, {
        readonly internalType: "contract IGlvWithdrawalHandler";
        readonly name: "_glvWithdrawalHandler";
        readonly type: "address";
    }, {
        readonly internalType: "contract IExternalHandler";
        readonly name: "_externalHandler";
        readonly type: "address";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "constructor";
}, {
    readonly inputs: readonly [];
    readonly name: "EmptyGlvDeposit";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "EmptyGlvWithdrawal";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "EmptyHoldingAddress";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "EmptyReceiver";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }];
    readonly name: "EmptyTokenTranferGasLimit";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "msgSender";
        readonly type: "address";
    }];
    readonly name: "InvalidNativeTokenSender";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "receiver";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }];
    readonly name: "TokenTransferError";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "msgSender";
        readonly type: "address";
    }, {
        readonly internalType: "string";
        readonly name: "role";
        readonly type: "string";
    }];
    readonly name: "Unauthorized";
    readonly type: "error";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "string";
        readonly name: "reason";
        readonly type: "string";
    }, {
        readonly indexed: false;
        readonly internalType: "bytes";
        readonly name: "returndata";
        readonly type: "bytes";
    }];
    readonly name: "TokenTransferReverted";
    readonly type: "event";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }];
    readonly name: "cancelGlvDeposit";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }];
    readonly name: "cancelGlvWithdrawal";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "glv";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "market";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "receiver";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "callbackContract";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "uiFeeReceiver";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "initialLongToken";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "initialShortToken";
                readonly type: "address";
            }, {
                readonly internalType: "address[]";
                readonly name: "longTokenSwapPath";
                readonly type: "address[]";
            }, {
                readonly internalType: "address[]";
                readonly name: "shortTokenSwapPath";
                readonly type: "address[]";
            }];
            readonly internalType: "struct IGlvDepositUtils.CreateGlvDepositParamsAddresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly internalType: "uint256";
            readonly name: "minGlvTokens";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "executionFee";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "callbackGasLimit";
            readonly type: "uint256";
        }, {
            readonly internalType: "bool";
            readonly name: "shouldUnwrapNativeToken";
            readonly type: "bool";
        }, {
            readonly internalType: "bool";
            readonly name: "isMarketTokenDeposit";
            readonly type: "bool";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "dataList";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct IGlvDepositUtils.CreateGlvDepositParams";
        readonly name: "params";
        readonly type: "tuple";
    }];
    readonly name: "createGlvDeposit";
    readonly outputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "";
        readonly type: "bytes32";
    }];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "receiver";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "callbackContract";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "uiFeeReceiver";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "market";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "glv";
                readonly type: "address";
            }, {
                readonly internalType: "address[]";
                readonly name: "longTokenSwapPath";
                readonly type: "address[]";
            }, {
                readonly internalType: "address[]";
                readonly name: "shortTokenSwapPath";
                readonly type: "address[]";
            }];
            readonly internalType: "struct IGlvWithdrawalUtils.CreateGlvWithdrawalParamsAddresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly internalType: "uint256";
            readonly name: "minLongTokenAmount";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "minShortTokenAmount";
            readonly type: "uint256";
        }, {
            readonly internalType: "bool";
            readonly name: "shouldUnwrapNativeToken";
            readonly type: "bool";
        }, {
            readonly internalType: "uint256";
            readonly name: "executionFee";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "callbackGasLimit";
            readonly type: "uint256";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "dataList";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct IGlvWithdrawalUtils.CreateGlvWithdrawalParams";
        readonly name: "params";
        readonly type: "tuple";
    }];
    readonly name: "createGlvWithdrawal";
    readonly outputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "";
        readonly type: "bytes32";
    }];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "dataStore";
    readonly outputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "eventEmitter";
    readonly outputs: readonly [{
        readonly internalType: "contract EventEmitter";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "externalHandler";
    readonly outputs: readonly [{
        readonly internalType: "contract IExternalHandler";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "glvDepositHandler";
    readonly outputs: readonly [{
        readonly internalType: "contract IGlvDepositHandler";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "glvWithdrawalHandler";
    readonly outputs: readonly [{
        readonly internalType: "contract IGlvWithdrawalHandler";
        readonly name: "";
        readonly type: "address";
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
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "roleStore";
    readonly outputs: readonly [{
        readonly internalType: "contract RoleStore";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "router";
    readonly outputs: readonly [{
        readonly internalType: "contract Router";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "receiver";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }];
    readonly name: "sendNativeToken";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "receiver";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }];
    readonly name: "sendTokens";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "receiver";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }];
    readonly name: "sendWnt";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }, {
        readonly components: readonly [{
            readonly internalType: "address[]";
            readonly name: "primaryTokens";
            readonly type: "address[]";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "min";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "max";
                readonly type: "uint256";
            }];
            readonly internalType: "struct Price.Props[]";
            readonly name: "primaryPrices";
            readonly type: "tuple[]";
        }, {
            readonly internalType: "uint256";
            readonly name: "minTimestamp";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "maxTimestamp";
            readonly type: "uint256";
        }];
        readonly internalType: "struct OracleUtils.SimulatePricesParams";
        readonly name: "simulatedOracleParams";
        readonly type: "tuple";
    }];
    readonly name: "simulateExecuteGlvDeposit";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }, {
        readonly components: readonly [{
            readonly internalType: "address[]";
            readonly name: "primaryTokens";
            readonly type: "address[]";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "min";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "max";
                readonly type: "uint256";
            }];
            readonly internalType: "struct Price.Props[]";
            readonly name: "primaryPrices";
            readonly type: "tuple[]";
        }, {
            readonly internalType: "uint256";
            readonly name: "minTimestamp";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "maxTimestamp";
            readonly type: "uint256";
        }];
        readonly internalType: "struct OracleUtils.SimulatePricesParams";
        readonly name: "simulatedOracleParams";
        readonly type: "tuple";
    }];
    readonly name: "simulateExecuteGlvWithdrawal";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly components: readonly [{
            readonly internalType: "address[]";
            readonly name: "primaryTokens";
            readonly type: "address[]";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "min";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "max";
                readonly type: "uint256";
            }];
            readonly internalType: "struct Price.Props[]";
            readonly name: "primaryPrices";
            readonly type: "tuple[]";
        }, {
            readonly internalType: "uint256";
            readonly name: "minTimestamp";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "maxTimestamp";
            readonly type: "uint256";
        }];
        readonly internalType: "struct OracleUtils.SimulatePricesParams";
        readonly name: "simulatedOracleParams";
        readonly type: "tuple";
    }];
    readonly name: "simulateExecuteLatestGlvDeposit";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly components: readonly [{
            readonly internalType: "address[]";
            readonly name: "primaryTokens";
            readonly type: "address[]";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "min";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "max";
                readonly type: "uint256";
            }];
            readonly internalType: "struct Price.Props[]";
            readonly name: "primaryPrices";
            readonly type: "tuple[]";
        }, {
            readonly internalType: "uint256";
            readonly name: "minTimestamp";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "maxTimestamp";
            readonly type: "uint256";
        }];
        readonly internalType: "struct OracleUtils.SimulatePricesParams";
        readonly name: "simulatedOracleParams";
        readonly type: "tuple";
    }];
    readonly name: "simulateExecuteLatestGlvWithdrawal";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly stateMutability: "payable";
    readonly type: "receive";
}];
export default _default;
