declare const _default: readonly [{
    readonly inputs: readonly [{
        readonly internalType: "contract RoleStore";
        readonly name: "_roleStore";
        readonly type: "address";
    }];
    readonly stateMutability: "nonpayable";
    readonly type: "constructor";
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
        readonly internalType: "address";
        readonly name: "msgSender";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "string";
        readonly name: "eventName";
        readonly type: "string";
    }, {
        readonly indexed: true;
        readonly internalType: "string";
        readonly name: "eventNameHash";
        readonly type: "string";
    }, {
        readonly components: readonly [{
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address";
                    readonly name: "value";
                    readonly type: "address";
                }];
                readonly internalType: "struct EventUtils.AddressKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address[]";
                    readonly name: "value";
                    readonly type: "address[]";
                }];
                readonly internalType: "struct EventUtils.AddressArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.AddressItems";
            readonly name: "addressItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "value";
                    readonly type: "uint256";
                }];
                readonly internalType: "struct EventUtils.UintKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256[]";
                    readonly name: "value";
                    readonly type: "uint256[]";
                }];
                readonly internalType: "struct EventUtils.UintArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.UintItems";
            readonly name: "uintItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256";
                    readonly name: "value";
                    readonly type: "int256";
                }];
                readonly internalType: "struct EventUtils.IntKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256[]";
                    readonly name: "value";
                    readonly type: "int256[]";
                }];
                readonly internalType: "struct EventUtils.IntArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.IntItems";
            readonly name: "intItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool";
                    readonly name: "value";
                    readonly type: "bool";
                }];
                readonly internalType: "struct EventUtils.BoolKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool[]";
                    readonly name: "value";
                    readonly type: "bool[]";
                }];
                readonly internalType: "struct EventUtils.BoolArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BoolItems";
            readonly name: "boolItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32";
                    readonly name: "value";
                    readonly type: "bytes32";
                }];
                readonly internalType: "struct EventUtils.Bytes32KeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32[]";
                    readonly name: "value";
                    readonly type: "bytes32[]";
                }];
                readonly internalType: "struct EventUtils.Bytes32ArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.Bytes32Items";
            readonly name: "bytes32Items";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes";
                    readonly name: "value";
                    readonly type: "bytes";
                }];
                readonly internalType: "struct EventUtils.BytesKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes[]";
                    readonly name: "value";
                    readonly type: "bytes[]";
                }];
                readonly internalType: "struct EventUtils.BytesArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BytesItems";
            readonly name: "bytesItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string";
                    readonly name: "value";
                    readonly type: "string";
                }];
                readonly internalType: "struct EventUtils.StringKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string[]";
                    readonly name: "value";
                    readonly type: "string[]";
                }];
                readonly internalType: "struct EventUtils.StringArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.StringItems";
            readonly name: "stringItems";
            readonly type: "tuple";
        }];
        readonly indexed: false;
        readonly internalType: "struct EventUtils.EventLogData";
        readonly name: "eventData";
        readonly type: "tuple";
    }];
    readonly name: "EventLog";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "msgSender";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "string";
        readonly name: "eventName";
        readonly type: "string";
    }, {
        readonly indexed: true;
        readonly internalType: "string";
        readonly name: "eventNameHash";
        readonly type: "string";
    }, {
        readonly indexed: true;
        readonly internalType: "bytes32";
        readonly name: "topic1";
        readonly type: "bytes32";
    }, {
        readonly components: readonly [{
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address";
                    readonly name: "value";
                    readonly type: "address";
                }];
                readonly internalType: "struct EventUtils.AddressKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address[]";
                    readonly name: "value";
                    readonly type: "address[]";
                }];
                readonly internalType: "struct EventUtils.AddressArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.AddressItems";
            readonly name: "addressItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "value";
                    readonly type: "uint256";
                }];
                readonly internalType: "struct EventUtils.UintKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256[]";
                    readonly name: "value";
                    readonly type: "uint256[]";
                }];
                readonly internalType: "struct EventUtils.UintArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.UintItems";
            readonly name: "uintItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256";
                    readonly name: "value";
                    readonly type: "int256";
                }];
                readonly internalType: "struct EventUtils.IntKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256[]";
                    readonly name: "value";
                    readonly type: "int256[]";
                }];
                readonly internalType: "struct EventUtils.IntArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.IntItems";
            readonly name: "intItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool";
                    readonly name: "value";
                    readonly type: "bool";
                }];
                readonly internalType: "struct EventUtils.BoolKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool[]";
                    readonly name: "value";
                    readonly type: "bool[]";
                }];
                readonly internalType: "struct EventUtils.BoolArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BoolItems";
            readonly name: "boolItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32";
                    readonly name: "value";
                    readonly type: "bytes32";
                }];
                readonly internalType: "struct EventUtils.Bytes32KeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32[]";
                    readonly name: "value";
                    readonly type: "bytes32[]";
                }];
                readonly internalType: "struct EventUtils.Bytes32ArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.Bytes32Items";
            readonly name: "bytes32Items";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes";
                    readonly name: "value";
                    readonly type: "bytes";
                }];
                readonly internalType: "struct EventUtils.BytesKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes[]";
                    readonly name: "value";
                    readonly type: "bytes[]";
                }];
                readonly internalType: "struct EventUtils.BytesArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BytesItems";
            readonly name: "bytesItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string";
                    readonly name: "value";
                    readonly type: "string";
                }];
                readonly internalType: "struct EventUtils.StringKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string[]";
                    readonly name: "value";
                    readonly type: "string[]";
                }];
                readonly internalType: "struct EventUtils.StringArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.StringItems";
            readonly name: "stringItems";
            readonly type: "tuple";
        }];
        readonly indexed: false;
        readonly internalType: "struct EventUtils.EventLogData";
        readonly name: "eventData";
        readonly type: "tuple";
    }];
    readonly name: "EventLog1";
    readonly type: "event";
}, {
    readonly anonymous: false;
    readonly inputs: readonly [{
        readonly indexed: false;
        readonly internalType: "address";
        readonly name: "msgSender";
        readonly type: "address";
    }, {
        readonly indexed: false;
        readonly internalType: "string";
        readonly name: "eventName";
        readonly type: "string";
    }, {
        readonly indexed: true;
        readonly internalType: "string";
        readonly name: "eventNameHash";
        readonly type: "string";
    }, {
        readonly indexed: true;
        readonly internalType: "bytes32";
        readonly name: "topic1";
        readonly type: "bytes32";
    }, {
        readonly indexed: true;
        readonly internalType: "bytes32";
        readonly name: "topic2";
        readonly type: "bytes32";
    }, {
        readonly components: readonly [{
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address";
                    readonly name: "value";
                    readonly type: "address";
                }];
                readonly internalType: "struct EventUtils.AddressKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address[]";
                    readonly name: "value";
                    readonly type: "address[]";
                }];
                readonly internalType: "struct EventUtils.AddressArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.AddressItems";
            readonly name: "addressItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "value";
                    readonly type: "uint256";
                }];
                readonly internalType: "struct EventUtils.UintKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256[]";
                    readonly name: "value";
                    readonly type: "uint256[]";
                }];
                readonly internalType: "struct EventUtils.UintArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.UintItems";
            readonly name: "uintItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256";
                    readonly name: "value";
                    readonly type: "int256";
                }];
                readonly internalType: "struct EventUtils.IntKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256[]";
                    readonly name: "value";
                    readonly type: "int256[]";
                }];
                readonly internalType: "struct EventUtils.IntArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.IntItems";
            readonly name: "intItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool";
                    readonly name: "value";
                    readonly type: "bool";
                }];
                readonly internalType: "struct EventUtils.BoolKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool[]";
                    readonly name: "value";
                    readonly type: "bool[]";
                }];
                readonly internalType: "struct EventUtils.BoolArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BoolItems";
            readonly name: "boolItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32";
                    readonly name: "value";
                    readonly type: "bytes32";
                }];
                readonly internalType: "struct EventUtils.Bytes32KeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32[]";
                    readonly name: "value";
                    readonly type: "bytes32[]";
                }];
                readonly internalType: "struct EventUtils.Bytes32ArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.Bytes32Items";
            readonly name: "bytes32Items";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes";
                    readonly name: "value";
                    readonly type: "bytes";
                }];
                readonly internalType: "struct EventUtils.BytesKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes[]";
                    readonly name: "value";
                    readonly type: "bytes[]";
                }];
                readonly internalType: "struct EventUtils.BytesArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BytesItems";
            readonly name: "bytesItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string";
                    readonly name: "value";
                    readonly type: "string";
                }];
                readonly internalType: "struct EventUtils.StringKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string[]";
                    readonly name: "value";
                    readonly type: "string[]";
                }];
                readonly internalType: "struct EventUtils.StringArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.StringItems";
            readonly name: "stringItems";
            readonly type: "tuple";
        }];
        readonly indexed: false;
        readonly internalType: "struct EventUtils.EventLogData";
        readonly name: "eventData";
        readonly type: "tuple";
    }];
    readonly name: "EventLog2";
    readonly type: "event";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "topic1";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes";
        readonly name: "data";
        readonly type: "bytes";
    }];
    readonly name: "emitDataLog1";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "topic1";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes32";
        readonly name: "topic2";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes";
        readonly name: "data";
        readonly type: "bytes";
    }];
    readonly name: "emitDataLog2";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "topic1";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes32";
        readonly name: "topic2";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes32";
        readonly name: "topic3";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes";
        readonly name: "data";
        readonly type: "bytes";
    }];
    readonly name: "emitDataLog3";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "bytes32";
        readonly name: "topic1";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes32";
        readonly name: "topic2";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes32";
        readonly name: "topic3";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes32";
        readonly name: "topic4";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes";
        readonly name: "data";
        readonly type: "bytes";
    }];
    readonly name: "emitDataLog4";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "string";
        readonly name: "eventName";
        readonly type: "string";
    }, {
        readonly components: readonly [{
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address";
                    readonly name: "value";
                    readonly type: "address";
                }];
                readonly internalType: "struct EventUtils.AddressKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address[]";
                    readonly name: "value";
                    readonly type: "address[]";
                }];
                readonly internalType: "struct EventUtils.AddressArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.AddressItems";
            readonly name: "addressItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "value";
                    readonly type: "uint256";
                }];
                readonly internalType: "struct EventUtils.UintKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256[]";
                    readonly name: "value";
                    readonly type: "uint256[]";
                }];
                readonly internalType: "struct EventUtils.UintArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.UintItems";
            readonly name: "uintItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256";
                    readonly name: "value";
                    readonly type: "int256";
                }];
                readonly internalType: "struct EventUtils.IntKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256[]";
                    readonly name: "value";
                    readonly type: "int256[]";
                }];
                readonly internalType: "struct EventUtils.IntArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.IntItems";
            readonly name: "intItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool";
                    readonly name: "value";
                    readonly type: "bool";
                }];
                readonly internalType: "struct EventUtils.BoolKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool[]";
                    readonly name: "value";
                    readonly type: "bool[]";
                }];
                readonly internalType: "struct EventUtils.BoolArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BoolItems";
            readonly name: "boolItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32";
                    readonly name: "value";
                    readonly type: "bytes32";
                }];
                readonly internalType: "struct EventUtils.Bytes32KeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32[]";
                    readonly name: "value";
                    readonly type: "bytes32[]";
                }];
                readonly internalType: "struct EventUtils.Bytes32ArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.Bytes32Items";
            readonly name: "bytes32Items";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes";
                    readonly name: "value";
                    readonly type: "bytes";
                }];
                readonly internalType: "struct EventUtils.BytesKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes[]";
                    readonly name: "value";
                    readonly type: "bytes[]";
                }];
                readonly internalType: "struct EventUtils.BytesArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BytesItems";
            readonly name: "bytesItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string";
                    readonly name: "value";
                    readonly type: "string";
                }];
                readonly internalType: "struct EventUtils.StringKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string[]";
                    readonly name: "value";
                    readonly type: "string[]";
                }];
                readonly internalType: "struct EventUtils.StringArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.StringItems";
            readonly name: "stringItems";
            readonly type: "tuple";
        }];
        readonly internalType: "struct EventUtils.EventLogData";
        readonly name: "eventData";
        readonly type: "tuple";
    }];
    readonly name: "emitEventLog";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "string";
        readonly name: "eventName";
        readonly type: "string";
    }, {
        readonly internalType: "bytes32";
        readonly name: "topic1";
        readonly type: "bytes32";
    }, {
        readonly components: readonly [{
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address";
                    readonly name: "value";
                    readonly type: "address";
                }];
                readonly internalType: "struct EventUtils.AddressKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address[]";
                    readonly name: "value";
                    readonly type: "address[]";
                }];
                readonly internalType: "struct EventUtils.AddressArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.AddressItems";
            readonly name: "addressItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "value";
                    readonly type: "uint256";
                }];
                readonly internalType: "struct EventUtils.UintKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256[]";
                    readonly name: "value";
                    readonly type: "uint256[]";
                }];
                readonly internalType: "struct EventUtils.UintArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.UintItems";
            readonly name: "uintItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256";
                    readonly name: "value";
                    readonly type: "int256";
                }];
                readonly internalType: "struct EventUtils.IntKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256[]";
                    readonly name: "value";
                    readonly type: "int256[]";
                }];
                readonly internalType: "struct EventUtils.IntArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.IntItems";
            readonly name: "intItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool";
                    readonly name: "value";
                    readonly type: "bool";
                }];
                readonly internalType: "struct EventUtils.BoolKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool[]";
                    readonly name: "value";
                    readonly type: "bool[]";
                }];
                readonly internalType: "struct EventUtils.BoolArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BoolItems";
            readonly name: "boolItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32";
                    readonly name: "value";
                    readonly type: "bytes32";
                }];
                readonly internalType: "struct EventUtils.Bytes32KeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32[]";
                    readonly name: "value";
                    readonly type: "bytes32[]";
                }];
                readonly internalType: "struct EventUtils.Bytes32ArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.Bytes32Items";
            readonly name: "bytes32Items";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes";
                    readonly name: "value";
                    readonly type: "bytes";
                }];
                readonly internalType: "struct EventUtils.BytesKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes[]";
                    readonly name: "value";
                    readonly type: "bytes[]";
                }];
                readonly internalType: "struct EventUtils.BytesArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BytesItems";
            readonly name: "bytesItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string";
                    readonly name: "value";
                    readonly type: "string";
                }];
                readonly internalType: "struct EventUtils.StringKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string[]";
                    readonly name: "value";
                    readonly type: "string[]";
                }];
                readonly internalType: "struct EventUtils.StringArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.StringItems";
            readonly name: "stringItems";
            readonly type: "tuple";
        }];
        readonly internalType: "struct EventUtils.EventLogData";
        readonly name: "eventData";
        readonly type: "tuple";
    }];
    readonly name: "emitEventLog1";
    readonly outputs: readonly [];
    readonly stateMutability: "nonpayable";
    readonly type: "function";
}, {
    readonly inputs: readonly [{
        readonly internalType: "string";
        readonly name: "eventName";
        readonly type: "string";
    }, {
        readonly internalType: "bytes32";
        readonly name: "topic1";
        readonly type: "bytes32";
    }, {
        readonly internalType: "bytes32";
        readonly name: "topic2";
        readonly type: "bytes32";
    }, {
        readonly components: readonly [{
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address";
                    readonly name: "value";
                    readonly type: "address";
                }];
                readonly internalType: "struct EventUtils.AddressKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "address[]";
                    readonly name: "value";
                    readonly type: "address[]";
                }];
                readonly internalType: "struct EventUtils.AddressArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.AddressItems";
            readonly name: "addressItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256";
                    readonly name: "value";
                    readonly type: "uint256";
                }];
                readonly internalType: "struct EventUtils.UintKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "uint256[]";
                    readonly name: "value";
                    readonly type: "uint256[]";
                }];
                readonly internalType: "struct EventUtils.UintArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.UintItems";
            readonly name: "uintItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256";
                    readonly name: "value";
                    readonly type: "int256";
                }];
                readonly internalType: "struct EventUtils.IntKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "int256[]";
                    readonly name: "value";
                    readonly type: "int256[]";
                }];
                readonly internalType: "struct EventUtils.IntArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.IntItems";
            readonly name: "intItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool";
                    readonly name: "value";
                    readonly type: "bool";
                }];
                readonly internalType: "struct EventUtils.BoolKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bool[]";
                    readonly name: "value";
                    readonly type: "bool[]";
                }];
                readonly internalType: "struct EventUtils.BoolArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BoolItems";
            readonly name: "boolItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32";
                    readonly name: "value";
                    readonly type: "bytes32";
                }];
                readonly internalType: "struct EventUtils.Bytes32KeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes32[]";
                    readonly name: "value";
                    readonly type: "bytes32[]";
                }];
                readonly internalType: "struct EventUtils.Bytes32ArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.Bytes32Items";
            readonly name: "bytes32Items";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes";
                    readonly name: "value";
                    readonly type: "bytes";
                }];
                readonly internalType: "struct EventUtils.BytesKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "bytes[]";
                    readonly name: "value";
                    readonly type: "bytes[]";
                }];
                readonly internalType: "struct EventUtils.BytesArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.BytesItems";
            readonly name: "bytesItems";
            readonly type: "tuple";
        }, {
            readonly components: readonly [{
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string";
                    readonly name: "value";
                    readonly type: "string";
                }];
                readonly internalType: "struct EventUtils.StringKeyValue[]";
                readonly name: "items";
                readonly type: "tuple[]";
            }, {
                readonly components: readonly [{
                    readonly internalType: "string";
                    readonly name: "key";
                    readonly type: "string";
                }, {
                    readonly internalType: "string[]";
                    readonly name: "value";
                    readonly type: "string[]";
                }];
                readonly internalType: "struct EventUtils.StringArrayKeyValue[]";
                readonly name: "arrayItems";
                readonly type: "tuple[]";
            }];
            readonly internalType: "struct EventUtils.StringItems";
            readonly name: "stringItems";
            readonly type: "tuple";
        }];
        readonly internalType: "struct EventUtils.EventLogData";
        readonly name: "eventData";
        readonly type: "tuple";
    }];
    readonly name: "emitEventLog2";
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
}];
export default _default;
