import { Module } from "../base";
export declare class Accounts extends Module {
    get govTokenAddress(): any;
    getGovTokenDelegates(account?: string): Promise<any>;
}
