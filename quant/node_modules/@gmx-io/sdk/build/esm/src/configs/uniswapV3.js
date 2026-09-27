import { ARBITRUM } from "./chains";
const DEPLOYMENTS = {
    [ARBITRUM]: {
        positionManager: "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
        factory: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    },
};
export function getUniswapV3Deployment(chainId) {
    return DEPLOYMENTS[chainId];
}
export function hasUniswapV3Deployment(chainId) {
    return Boolean(getUniswapV3Deployment(chainId));
}
