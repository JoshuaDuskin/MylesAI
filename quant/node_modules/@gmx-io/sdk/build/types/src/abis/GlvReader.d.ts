declare const _default: readonly [{
    readonly inputs: readonly [];
    readonly name: "EmptyMarketTokenSupply";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "glv";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "market";
        readonly type: "address";
    }];
    readonly name: "GlvNegativeMarketPoolValue";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "start";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "end";
        readonly type: "uint256";
    }];
    readonly name: "getAccountGlvDeposits";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "glv";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "account";
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
                readonly name: "market";
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
            readonly internalType: "struct GlvDeposit.Addresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "marketTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "initialLongTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "initialShortTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minGlvTokens";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "updatedAtTime";
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
                readonly name: "srcChainId";
                readonly type: "uint256";
            }];
            readonly internalType: "struct GlvDeposit.Numbers";
            readonly name: "numbers";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "bool";
                readonly name: "shouldUnwrapNativeToken";
                readonly type: "bool";
            }, {
                readonly internalType: "bool";
                readonly name: "isMarketTokenDeposit";
                readonly type: "bool";
            }];
            readonly internalType: "struct GlvDeposit.Flags";
            readonly name: "flags";
            readonly type: "tuple";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "_dataList";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct GlvDeposit.Props[]";
        readonly name: "";
        readonly type: "tuple[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "start";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "end";
        readonly type: "uint256";
    }];
    readonly name: "getAccountGlvWithdrawals";
    readonly outputs: readonly [{
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
                readonly name: "account";
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
                readonly internalType: "address[]";
                readonly name: "longTokenSwapPath";
                readonly type: "address[]";
            }, {
                readonly internalType: "address[]";
                readonly name: "shortTokenSwapPath";
                readonly type: "address[]";
            }];
            readonly internalType: "struct GlvWithdrawal.Addresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "glvTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minLongTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minShortTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "updatedAtTime";
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
                readonly name: "srcChainId";
                readonly type: "uint256";
            }];
            readonly internalType: "struct GlvWithdrawal.Numbers";
            readonly name: "numbers";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "bool";
                readonly name: "shouldUnwrapNativeToken";
                readonly type: "bool";
            }];
            readonly internalType: "struct GlvWithdrawal.Flags";
            readonly name: "flags";
            readonly type: "tuple";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "_dataList";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct GlvWithdrawal.Props[]";
        readonly name: "";
        readonly type: "tuple[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "glv";
        readonly type: "address";
    }];
    readonly name: "getGlv";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly internalType: "address";
            readonly name: "glvToken";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "longToken";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "shortToken";
            readonly type: "address";
        }];
        readonly internalType: "struct Glv.Props";
        readonly name: "";
        readonly type: "tuple";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "bytes32";
        readonly name: "salt";
        readonly type: "bytes32";
    }];
    readonly name: "getGlvBySalt";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly internalType: "address";
            readonly name: "glvToken";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "longToken";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "shortToken";
            readonly type: "address";
        }];
        readonly internalType: "struct Glv.Props";
        readonly name: "";
        readonly type: "tuple";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }];
    readonly name: "getGlvDeposit";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "glv";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "account";
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
                readonly name: "market";
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
            readonly internalType: "struct GlvDeposit.Addresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "marketTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "initialLongTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "initialShortTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minGlvTokens";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "updatedAtTime";
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
                readonly name: "srcChainId";
                readonly type: "uint256";
            }];
            readonly internalType: "struct GlvDeposit.Numbers";
            readonly name: "numbers";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "bool";
                readonly name: "shouldUnwrapNativeToken";
                readonly type: "bool";
            }, {
                readonly internalType: "bool";
                readonly name: "isMarketTokenDeposit";
                readonly type: "bool";
            }];
            readonly internalType: "struct GlvDeposit.Flags";
            readonly name: "flags";
            readonly type: "tuple";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "_dataList";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct GlvDeposit.Props";
        readonly name: "";
        readonly type: "tuple";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "start";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "end";
        readonly type: "uint256";
    }];
    readonly name: "getGlvDeposits";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "glv";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "account";
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
                readonly name: "market";
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
            readonly internalType: "struct GlvDeposit.Addresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "marketTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "initialLongTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "initialShortTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minGlvTokens";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "updatedAtTime";
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
                readonly name: "srcChainId";
                readonly type: "uint256";
            }];
            readonly internalType: "struct GlvDeposit.Numbers";
            readonly name: "numbers";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "bool";
                readonly name: "shouldUnwrapNativeToken";
                readonly type: "bool";
            }, {
                readonly internalType: "bool";
                readonly name: "isMarketTokenDeposit";
                readonly type: "bool";
            }];
            readonly internalType: "struct GlvDeposit.Flags";
            readonly name: "flags";
            readonly type: "tuple";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "_dataList";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct GlvDeposit.Props[]";
        readonly name: "";
        readonly type: "tuple[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "glv";
        readonly type: "address";
    }];
    readonly name: "getGlvInfo";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "glvToken";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "longToken";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "shortToken";
                readonly type: "address";
            }];
            readonly internalType: "struct Glv.Props";
            readonly name: "glv";
            readonly type: "tuple";
        }, {
            readonly internalType: "address[]";
            readonly name: "markets";
            readonly type: "address[]";
        }];
        readonly internalType: "struct GlvReader.GlvInfo";
        readonly name: "";
        readonly type: "tuple";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "start";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "end";
        readonly type: "uint256";
    }];
    readonly name: "getGlvInfoList";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "glvToken";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "longToken";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "shortToken";
                readonly type: "address";
            }];
            readonly internalType: "struct Glv.Props";
            readonly name: "glv";
            readonly type: "tuple";
        }, {
            readonly internalType: "address[]";
            readonly name: "markets";
            readonly type: "address[]";
        }];
        readonly internalType: "struct GlvReader.GlvInfo[]";
        readonly name: "";
        readonly type: "tuple[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }];
    readonly name: "getGlvShift";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "glv";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "fromMarket";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "toMarket";
                readonly type: "address";
            }];
            readonly internalType: "struct GlvShift.Addresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "marketTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minMarketTokens";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "updatedAtTime";
                readonly type: "uint256";
            }];
            readonly internalType: "struct GlvShift.Numbers";
            readonly name: "numbers";
            readonly type: "tuple";
        }];
        readonly internalType: "struct GlvShift.Props";
        readonly name: "";
        readonly type: "tuple";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "start";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "end";
        readonly type: "uint256";
    }];
    readonly name: "getGlvShifts";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly components: readonly [{
                readonly internalType: "address";
                readonly name: "glv";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "fromMarket";
                readonly type: "address";
            }, {
                readonly internalType: "address";
                readonly name: "toMarket";
                readonly type: "address";
            }];
            readonly internalType: "struct GlvShift.Addresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "marketTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minMarketTokens";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "updatedAtTime";
                readonly type: "uint256";
            }];
            readonly internalType: "struct GlvShift.Numbers";
            readonly name: "numbers";
            readonly type: "tuple";
        }];
        readonly internalType: "struct GlvShift.Props[]";
        readonly name: "";
        readonly type: "tuple[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "marketAddresses";
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
        readonly name: "indexTokenPrices";
        readonly type: "tuple[]";
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
        readonly internalType: "struct Price.Props";
        readonly name: "longTokenPrice";
        readonly type: "tuple";
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
        readonly internalType: "struct Price.Props";
        readonly name: "shortTokenPrice";
        readonly type: "tuple";
    }, {
        readonly internalType: "address";
        readonly name: "glv";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "maximize";
        readonly type: "bool";
    }];
    readonly name: "getGlvTokenPrice";
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
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "address[]";
        readonly name: "marketAddresses";
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
        readonly name: "indexTokenPrices";
        readonly type: "tuple[]";
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
        readonly internalType: "struct Price.Props";
        readonly name: "longTokenPrice";
        readonly type: "tuple";
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
        readonly internalType: "struct Price.Props";
        readonly name: "shortTokenPrice";
        readonly type: "tuple";
    }, {
        readonly internalType: "address";
        readonly name: "glv";
        readonly type: "address";
    }, {
        readonly internalType: "bool";
        readonly name: "maximize";
        readonly type: "bool";
    }];
    readonly name: "getGlvValue";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }];
    readonly name: "getGlvWithdrawal";
    readonly outputs: readonly [{
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
                readonly name: "account";
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
                readonly internalType: "address[]";
                readonly name: "longTokenSwapPath";
                readonly type: "address[]";
            }, {
                readonly internalType: "address[]";
                readonly name: "shortTokenSwapPath";
                readonly type: "address[]";
            }];
            readonly internalType: "struct GlvWithdrawal.Addresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "glvTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minLongTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minShortTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "updatedAtTime";
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
                readonly name: "srcChainId";
                readonly type: "uint256";
            }];
            readonly internalType: "struct GlvWithdrawal.Numbers";
            readonly name: "numbers";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "bool";
                readonly name: "shouldUnwrapNativeToken";
                readonly type: "bool";
            }];
            readonly internalType: "struct GlvWithdrawal.Flags";
            readonly name: "flags";
            readonly type: "tuple";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "_dataList";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct GlvWithdrawal.Props";
        readonly name: "";
        readonly type: "tuple";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "start";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "end";
        readonly type: "uint256";
    }];
    readonly name: "getGlvWithdrawals";
    readonly outputs: readonly [{
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
                readonly name: "account";
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
                readonly internalType: "address[]";
                readonly name: "longTokenSwapPath";
                readonly type: "address[]";
            }, {
                readonly internalType: "address[]";
                readonly name: "shortTokenSwapPath";
                readonly type: "address[]";
            }];
            readonly internalType: "struct GlvWithdrawal.Addresses";
            readonly name: "addresses";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "uint256";
                readonly name: "glvTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minLongTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "minShortTokenAmount";
                readonly type: "uint256";
            }, {
                readonly internalType: "uint256";
                readonly name: "updatedAtTime";
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
                readonly name: "srcChainId";
                readonly type: "uint256";
            }];
            readonly internalType: "struct GlvWithdrawal.Numbers";
            readonly name: "numbers";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly internalType: "bool";
                readonly name: "shouldUnwrapNativeToken";
                readonly type: "bool";
            }];
            readonly internalType: "struct GlvWithdrawal.Flags";
            readonly name: "flags";
            readonly type: "tuple";
        }, {
            readonly internalType: "bytes32[]";
            readonly name: "_dataList";
            readonly type: "bytes32[]";
        }];
        readonly internalType: "struct GlvWithdrawal.Props[]";
        readonly name: "";
        readonly type: "tuple[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "contract DataStore";
        readonly name: "dataStore";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "start";
        readonly type: "uint256";
    }, {
        readonly internalType: "uint256";
        readonly name: "end";
        readonly type: "uint256";
    }];
    readonly name: "getGlvs";
    readonly outputs: readonly [{
        readonly components: readonly [{
            readonly internalType: "address";
            readonly name: "glvToken";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "longToken";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "shortToken";
            readonly type: "address";
        }];
        readonly internalType: "struct Glv.Props[]";
        readonly name: "";
        readonly type: "tuple[]";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}];
export default _default;
