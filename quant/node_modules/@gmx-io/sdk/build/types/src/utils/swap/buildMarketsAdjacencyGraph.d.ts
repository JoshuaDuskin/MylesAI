import type { MarketConfig } from "../../configs/markets";
type FromTokenAddress = string;
type ToTokenAddress = string;
type MarketAddress = string;
export type MarketsGraph = {
    [from: FromTokenAddress]: {
        [to: ToTokenAddress]: MarketAddress[];
    };
};
export declare function buildMarketsAdjacencyGraph(marketsMap: Record<string, MarketConfig>): MarketsGraph;
export {};
