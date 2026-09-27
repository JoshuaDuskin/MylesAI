import { ContractsChainId } from "./chains";
export type VenusVTokenConfig = {
    vTokenAddress: string;
    underlyingAddress: string;
    symbol: string;
};
export type VenusDeployment = {
    comptroller: string;
    poolRegistry: string;
    poolLens: string;
    nativeTokenGateway: string;
    vTokens: VenusVTokenConfig[];
};
export declare const VENUS_EXCHANGE_RATE_DECIMALS = 18n;
export declare function getVenusDeployment(chainId: ContractsChainId): VenusDeployment | undefined;
export declare function hasVenusDeployment(chainId: ContractsChainId): boolean;
