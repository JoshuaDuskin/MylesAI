declare const _default: readonly [{
    readonly inputs: readonly [{
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
        readonly internalType: "contract ClaimVault";
        readonly name: "_claimVault";
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
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "existingDistributionId";
        readonly type: "uint256";
    }];
    readonly name: "DuplicateClaimTerms";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "EmptyAccount";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }];
    readonly name: "EmptyClaimableAmount";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "EmptyReceiver";
    readonly type: "error";
}, {
    readonly inputs: readonly [];
    readonly name: "EmptyToken";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }];
    readonly name: "InsufficientFunds";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "recoveredSigner";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "expectedSigner";
        readonly type: "address";
    }];
    readonly name: "InvalidClaimTermsSignature";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "expectedSigner";
        readonly type: "address";
    }];
    readonly name: "InvalidClaimTermsSignatureForContract";
    readonly type: "error";
}, {
    readonly inputs: readonly [{
        readonly internalType: "string";
        readonly name: "reason";
        readonly type: "string";
    }];
    readonly name: "InvalidParams";
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
        readonly components: readonly [{
            readonly internalType: "address";
            readonly name: "token";
            readonly type: "address";
        }, {
            readonly internalType: "uint256";
            readonly name: "distributionId";
            readonly type: "uint256";
        }, {
            readonly internalType: "bytes";
            readonly name: "termsSignature";
            readonly type: "bytes";
        }, {
            readonly internalType: "string";
            readonly name: "acceptedTerms";
            readonly type: "string";
        }];
        readonly internalType: "struct ClaimHandler.ClaimParam[]";
        readonly name: "params";
        readonly type: "tuple[]";
    }, {
        readonly internalType: "address";
        readonly name: "receiver";
        readonly type: "address";
    }];
    readonly name: "acceptTermsAndClaim";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [];
    readonly name: "claimVault";
    readonly outputs: readonly [{
        readonly internalType: "contract ClaimVault";
        readonly name: "";
        readonly type: "address";
    }];
    readonly stateMutability: "view";
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
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly internalType: "uint256";
        readonly name: "distributionId";
        readonly type: "uint256";
    }, {
        readonly components: readonly [{
            readonly internalType: "address";
            readonly name: "account";
            readonly type: "address";
        }, {
            readonly internalType: "uint256";
            readonly name: "amount";
            readonly type: "uint256";
        }];
        readonly internalType: "struct ClaimUtils.DepositParam[]";
        readonly name: "params";
        readonly type: "tuple[]";
    }];
    readonly name: "depositFunds";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
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
        readonly internalType: "address";
        readonly name: "account";
        readonly type: "address";
    }, {
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly internalType: "uint256[]";
        readonly name: "distributionIds";
        readonly type: "uint256[]";
    }];
    readonly name: "getClaimableAmount";
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
        readonly name: "token";
        readonly type: "address";
    }];
    readonly name: "getTotalClaimableAmount";
    readonly outputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "";
        readonly type: "uint256";
    }];
    readonly stateMutability: "view";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "distributionId";
        readonly type: "uint256";
    }];
    readonly name: "removeTerms";
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
    readonly inputs: readonly [{
        readonly internalType: "uint256";
        readonly name: "distributionId";
        readonly type: "uint256";
    }, {
        readonly internalType: "string";
        readonly name: "terms";
        readonly type: "string";
    }];
    readonly name: "setTerms";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly components: readonly [{
            readonly internalType: "address";
            readonly name: "token";
            readonly type: "address";
        }, {
            readonly internalType: "uint256";
            readonly name: "distributionId";
            readonly type: "uint256";
        }, {
            readonly internalType: "address";
            readonly name: "fromAccount";
            readonly type: "address";
        }, {
            readonly internalType: "address";
            readonly name: "toAccount";
            readonly type: "address";
        }];
        readonly internalType: "struct ClaimHandler.TransferClaimParam[]";
        readonly name: "params";
        readonly type: "tuple[]";
    }];
    readonly name: "transferClaim";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "address";
        readonly name: "token";
        readonly type: "address";
    }, {
        readonly components: readonly [{
            readonly internalType: "address";
            readonly name: "account";
            readonly type: "address";
        }, {
            readonly internalType: "uint256";
            readonly name: "distributionId";
            readonly type: "uint256";
        }];
        readonly internalType: "struct ClaimHandler.WithdrawParam[]";
        readonly name: "params";
        readonly type: "tuple[]";
    }, {
        readonly internalType: "address";
        readonly name: "receiver";
        readonly type: "address";
    }];
    readonly name: "withdrawFunds";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}];
export default _default;
