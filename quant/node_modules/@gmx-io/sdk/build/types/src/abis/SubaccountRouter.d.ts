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
        readonly internalType: "contract IOrderHandler";
        readonly name: "_orderHandler";
        readonly type: "address";
    }, {
        readonly internalType: "contract OrderVault";
        readonly name: "_orderVault";
        readonly type: "address";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "constructor";
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
        readonly internalType: "address";
        readonly name: "subaccount";
        readonly type: "address";
    }];
    readonly name: "addSubaccount";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "key";
        readonly type: "bytes32";
    }];
    readonly name: "cancelOrder";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
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
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "subaccount";
        readonly type: "address";
    }];
    readonly name: "removeSubaccount";
    readonly outputs: readonly [];
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
        readonly internalType: "address";
        readonly name: "subaccount";
        readonly type: "address";
    }, {
        readonly internalType: "bytes32";
        readonly name: "integrationId";
        readonly type: "bytes32";
    }];
    readonly name: "setIntegrationId";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "subaccount";
        readonly type: "address";
    }, {
        readonly internalType: "bytes32";
        readonly name: "actionType";
        readonly type: "bytes32";
    }, {
        readonly internalType: "uint256";
        readonly name: "maxAllowedCount";
        readonly type: "uint256";
    }];
    readonly name: "setMaxAllowedSubaccountActionCount";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "subaccount";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "amount";
        readonly type: "uint256";
    }];
    readonly name: "setSubaccountAutoTopUpAmount";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "subaccount";
        readonly type: "address";
    }, {
        readonly internalType: "bytes32";
        readonly name: "actionType";
        readonly type: "bytes32";
    }, {
        readonly internalType: "uint256";
        readonly name: "expiresAt";
        readonly type: "uint256";
    }];
    readonly name: "setSubaccountExpiresAt";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
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
    }];
    readonly name: "updateOrder";
    readonly outputs: readonly [];
    readonly stateMutability: "payable";
    readonly type: "function";
}, {
    readonly stateMutability: "payable";
    readonly type: "receive";
}];
export default _default;
