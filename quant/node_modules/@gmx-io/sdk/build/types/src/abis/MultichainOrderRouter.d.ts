declare const _default: readonly [{
    readonly inputs: readonly [{
        readonly components: readonly [{
            readonly internalType: "contract Router";
            readonly name: "router";
            readonly type: "address";
        }, {
            readonly internalType: "contract RoleStore";
            readonly name: "roleStore";
            readonly type: "address";
        }, {
            readonly internalType: "contract DataStore";
            readonly name: "dataStore";
            readonly type: "address";
        }, {
            readonly internalType: "contract EventEmitter";
            readonly name: "eventEmitter";
            readonly type: "address";
        }, {
            readonly internalType: "contract IOracle";
            readonly name: "oracle";
            readonly type: "address";
        }, {
            readonly internalType: "contract OrderVault";
            readonly name: "orderVault";
            readonly type: "address";
        }, {
            readonly internalType: "contract IOrderHandler";
            readonly name: "orderHandler";
            readonly type: "address";
        }, {
            readonly internalType: "contract ISwapHandler";
            readonly name: "swapHandler";
            readonly type: "address";
        }, {
            readonly internalType: "contract IExternalHandler";
            readonly name: "externalHandler";
            readonly type: "address";
        }, {
            readonly internalType: "contract MultichainVault";
            readonly name: "multichainVault";
            readonly type: "address";
        }];
        readonly internalType: "struct MultichainRouter.BaseConstructorParams";
        readonly name: "params";
        readonly type: "tuple";
    }, {
        readonly internalType: "contract IReferralStorage";
        readonly name: "_referralStorage";
        readonly type: "address";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "constructor";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "currentTimestamp";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "deadline";
        readonly type: "uint256";
    }];
    readonly name: "DeadlinePassed";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }];
    readonly name: "DisabledFeature";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "EmptyHoldingAddress";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "EmptyOrder";
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
        readonly internalType: "uint256";
        readonly name: "requiredRelayFee";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "availableFeeAmount";
        readonly type: "uint256";
    }];
    readonly name: "InsufficientRelayFee";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "desChainId";
        readonly type: "uint256";
    }];
    readonly name: "InvalidDestinationChainId";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "sendTokensLength";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "sendAmountsLength";
        readonly type: "uint256";
    }];
    readonly name: "InvalidExternalCalls";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "spender";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "expectedSpender";
        readonly type: "address";
    }];
    readonly name: "InvalidPermitSpender";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "srcChainId";
        readonly type: "uint256";
    }];
    readonly name: "InvalidSrcChainId";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "digest";
        readonly type: "bytes32";
    }];
    readonly name: "InvalidUserDigest";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "feeUsd";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "maxFeeUsd";
        readonly type: "uint256";
    }];
    readonly name: "MaxRelayFeeSwapForSubaccountExceeded";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "NonEmptyExternalCallsForSubaccountOrder";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "code";
        readonly type: "bytes32";
    }];
    readonly name: "ReferralCodeAlreadyExists";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "RelayEmptyBatch";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "TokenPermitsNotAllowedForMultichain";
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
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "feeToken";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "expectedFeeToken";
        readonly type: "address";
    }];
    readonly name: "UnexpectedRelayFeeToken";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "feeToken";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "expectedFeeToken";
        readonly type: "address";
    }];
    readonly name: "UnsupportedRelayFeeToken";
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
        readonly components: readonly [{
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
            readonly internalType: "struct IRelayUtils.ExternalCalls";
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
            readonly internalType: "struct IRelayUtils.TokenPermit[]";
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
            readonly internalType: "struct IRelayUtils.FeeParams";
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
            readonly internalType: "bytes";
            readonly name: "signature";
            readonly type: "bytes";
        }, {
            readonly internalType: "uint256";
            readonly name: "desChainId";
            readonly type: "uint256";
        }];
        readonly internalType: "struct IRelayUtils.RelayParams";
        readonly name: "relayParams";
        readonly type: "tuple";
    }, {
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "srcChainId";
        readonly type: "uint256";
    }, {
        readonly components: readonly [{
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "address";
                    readonly name: "receiver";
                    readonly type: "address";
                }, {
                    readonly internalType: "address";
                    readonly name: "cancellationReceiver";
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
                    readonly name: "initialCollateralToken";
                    readonly type: "address";
                }, {
                    readonly internalType: "address[]";
                    readonly name: "swapPath";
                    readonly type: "address[]";
                }];
                readonly internalType: "struct IBaseOrderUtils.CreateOrderParamsAddresses";
                readonly name: "addresses";
                readonly type: "tuple";
            }, {
                readonly components: readonly [{
                    readonly internalType: "uint256";
                    readonly name: "sizeDeltaUsd";
                    readonly type: "uint256";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "initialCollateralDeltaAmount";
                    readonly type: "uint256";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "triggerPrice";
                    readonly type: "uint256";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "acceptablePrice";
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
                    readonly internalType: "uint256";
                    readonly name: "minOutputAmount";
                    readonly type: "uint256";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "validFromTime";
                    readonly type: "uint256";
                }];
                readonly internalType: "struct IBaseOrderUtils.CreateOrderParamsNumbers";
                readonly name: "numbers";
                readonly type: "tuple";
            }, {
                readonly internalType: "enum Order.OrderType";
                readonly name: "orderType";
                readonly type: "uint8";
            }, {
                readonly internalType: "enum Order.DecreasePositionSwapType";
                readonly name: "decreasePositionSwapType";
                readonly type: "uint8";
            }, {
                readonly internalType: "bool";
                readonly name: "isLong";
                readonly type: "bool";
            }, {
                readonly internalType: "bool";
                readonly name: "shouldUnwrapNativeToken";
                readonly type: "bool";
            }, {
                readonly internalType: "bool";
                readonly name: "autoCancel";
                readonly type: "bool";
            }, {
                readonly internalType: "bytes32";
                readonly name: "referralCode";
                readonly type: "bytes32";
            }, {
                readonly internalType: "bytes32[]";
                readonly name: "dataList";
                readonly type: "bytes32[]";
            }];
            readonly internalType: "struct IBaseOrderUtils.CreateOrderParams[]";
            readonly name: "createOrderParamsList";
            readonly type: "tuple[]";
        }, {
            readonly components: readonly [{
                readonly internalType: "bytes32";
                readonly name: "key";
                readonly type: "bytes32";
            }, {
                readonly internalType: "uint256";
                readonly name: "sizeDeltaUsd";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "acceptablePrice";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "triggerPrice";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minOutputAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "validFromTime";
                readonly type: "uint256";
            }, {
                readonly internalType: "bool";
                readonly name: "autoCancel";
                readonly type: "bool";
            }, {
                readonly internalType: "uint256";
                readonly name: "executionFeeIncrease";
                readonly type: "uint256";
            }];
            readonly internalType: "struct IRelayUtils.UpdateOrderParams[]";
            readonly name: "updateOrderParamsList";
            readonly type: "tuple[]";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "cancelOrderKeys";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct IRelayUtils.BatchParams";
        readonly name: "params";
        readonly type: "tuple";
    }];
    readonly name: "batch";
    readonly outputs: readonly [{
        readonly internalType: "bytes32[]";
        readonly name: "";
        readonly type: "bytes32[]";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly components: readonly [{
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
            readonly internalType: "struct IRelayUtils.ExternalCalls";
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
            readonly internalType: "struct IRelayUtils.TokenPermit[]";
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
            readonly internalType: "struct IRelayUtils.FeeParams";
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
            readonly internalType: "bytes";
            readonly name: "signature";
            readonly type: "bytes";
        }, {
            readonly internalType: "uint256";
            readonly name: "desChainId";
            readonly type: "uint256";
        }];
        readonly internalType: "struct IRelayUtils.RelayParams";
        readonly name: "relayParams";
        readonly type: "tuple";
    }, {
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "srcChainId";
        readonly type: "uint256";
    }, {
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }];
    readonly name: "cancelOrder";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly components: readonly [{
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
            readonly internalType: "struct IRelayUtils.ExternalCalls";
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
            readonly internalType: "struct IRelayUtils.TokenPermit[]";
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
            readonly internalType: "struct IRelayUtils.FeeParams";
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
            readonly internalType: "bytes";
            readonly name: "signature";
            readonly type: "bytes";
        }, {
            readonly internalType: "uint256";
            readonly name: "desChainId";
            readonly type: "uint256";
        }];
        readonly internalType: "struct IRelayUtils.RelayParams";
        readonly name: "relayParams";
        readonly type: "tuple";
    }, {
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "srcChainId";
        readonly type: "uint256";
    }, {
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "receiver";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "cancellationReceiver";
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
                readonly name: "initialCollateralToken";
                readonly type: "address";
            }, {
                readonly internalType: "address[]";
                readonly name: "swapPath";
                readonly type: "address[]";
            }];
            readonly internalType: "struct IBaseOrderUtils.CreateOrderParamsAddresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "sizeDeltaUsd";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "initialCollateralDeltaAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "triggerPrice";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "acceptablePrice";
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
                readonly internalType: "uint256";
                readonly name: "minOutputAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "validFromTime";
                readonly type: "uint256";
            }];
            readonly internalType: "struct IBaseOrderUtils.CreateOrderParamsNumbers";
            readonly name: "numbers";
            readonly type: "tuple";
        }, {
            readonly internalType: "enum Order.OrderType";
            readonly name: "orderType";
            readonly type: "uint8";
        }, {
            readonly internalType: "enum Order.DecreasePositionSwapType";
            readonly name: "decreasePositionSwapType";
            readonly type: "uint8";
        }, {
            readonly internalType: "bool";
            readonly name: "isLong";
            readonly type: "bool";
        }, {
            readonly internalType: "bool";
            readonly name: "shouldUnwrapNativeToken";
            readonly type: "bool";
        }, {
            readonly internalType: "bool";
            readonly name: "autoCancel";
            readonly type: "bool";
        }, {
            readonly internalType: "bytes32";
            readonly name: "referralCode";
            readonly type: "bytes32";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "dataList";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct IBaseOrderUtils.CreateOrderParams";
        readonly name: "params";
        readonly type: "tuple";
    }];
    readonly name: "createOrder";
    readonly outputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "";
        readonly type: "bytes32";
    }];
    readonly stateMutability: "nonpayable";
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
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "";
        readonly type: "bytes32";
    }];
    readonly name: "digests";
    readonly outputs: readonly [{
        readonly internalType: "bool";
        readonly name: "";
        readonly type: "bool";
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
    readonly name: "multichainVault";
    readonly outputs: readonly [{
        readonly internalType: "contract MultichainVault";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "oracle";
    readonly outputs: readonly [{
        readonly internalType: "contract IOracle";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "orderHandler";
    readonly outputs: readonly [{
        readonly internalType: "contract IOrderHandler";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "orderVault";
    readonly outputs: readonly [{
        readonly internalType: "contract OrderVault";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "referralStorage";
    readonly outputs: readonly [{
        readonly internalType: "contract IReferralStorage";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly components: readonly [{
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
            readonly internalType: "struct IRelayUtils.ExternalCalls";
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
            readonly internalType: "struct IRelayUtils.TokenPermit[]";
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
            readonly internalType: "struct IRelayUtils.FeeParams";
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
            readonly internalType: "bytes";
            readonly name: "signature";
            readonly type: "bytes";
        }, {
            readonly internalType: "uint256";
            readonly name: "desChainId";
            readonly type: "uint256";
        }];
        readonly internalType: "struct IRelayUtils.RelayParams";
        readonly name: "relayParams";
        readonly type: "tuple";
    }, {
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "srcChainId";
        readonly type: "uint256";
    }, {
        readonly internalType: "bytes32";
        readonly name: "referralCode";
        readonly type: "bytes32";
    }];
    readonly name: "registerCode";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
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
        readonly components: readonly [{
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
            readonly internalType: "struct IRelayUtils.ExternalCalls";
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
            readonly internalType: "struct IRelayUtils.TokenPermit[]";
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
            readonly internalType: "struct IRelayUtils.FeeParams";
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
            readonly internalType: "bytes";
            readonly name: "signature";
            readonly type: "bytes";
        }, {
            readonly internalType: "uint256";
            readonly name: "desChainId";
            readonly type: "uint256";
        }];
        readonly internalType: "struct IRelayUtils.RelayParams";
        readonly name: "relayParams";
        readonly type: "tuple";
    }, {
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "srcChainId";
        readonly type: "uint256";
    }, {
        readonly internalType: "bytes32";
        readonly name: "referralCode";
        readonly type: "bytes32";
    }];
    readonly name: "setTraderReferralCode";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "swapHandler";
    readonly outputs: readonly [{
        readonly internalType: "contract ISwapHandler";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly components: readonly [{
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
            readonly internalType: "struct IRelayUtils.ExternalCalls";
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
            readonly internalType: "struct IRelayUtils.TokenPermit[]";
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
            readonly internalType: "struct IRelayUtils.FeeParams";
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
            readonly internalType: "bytes";
            readonly name: "signature";
            readonly type: "bytes";
        }, {
            readonly internalType: "uint256";
            readonly name: "desChainId";
            readonly type: "uint256";
        }];
        readonly internalType: "struct IRelayUtils.RelayParams";
        readonly name: "relayParams";
        readonly type: "tuple";
    }, {
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "srcChainId";
        readonly type: "uint256";
    }, {
        readonly components: readonly [{
            readonly internalType: "bytes32";
            readonly name: "key";
            readonly type: "bytes32";
        }, {
            readonly internalType: "uint256";
            readonly name: "sizeDeltaUsd";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "acceptablePrice";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "triggerPrice";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "minOutputAmount";
            readonly type: "uint256";
        }, {
            readonly internalType: "uint256";
            readonly name: "validFromTime";
            readonly type: "uint256";
        }, {
            readonly internalType: "bool";
            readonly name: "autoCancel";
            readonly type: "bool";
        }, {
            readonly internalType: "uint256";
            readonly name: "executionFeeIncrease";
            readonly type: "uint256";
        }];
        readonly internalType: "struct IRelayUtils.UpdateOrderParams";
        readonly name: "params";
        readonly type: "tuple";
    }];
    readonly name: "updateOrder";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}];
export default _default;
