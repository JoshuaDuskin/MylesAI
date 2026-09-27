import { ContractsChainId } from "./chains";
export type UniswapV3Deployment = {
    positionManager: string;
    factory: string;
};
export declare function getUniswapV3Deployment(chainId: ContractsChainId): UniswapV3Deployment | undefined;
export declare function hasUniswapV3Deployment(chainId: ContractsChainId): boolean;
