import { ClientConfig, MulticallBatchOptions } from "viem";
import { AnyChainId } from "./chains";
export declare const BATCH_CONFIGS: Record<AnyChainId, {
    http: MulticallBatchOptions;
    client: ClientConfig["batch"];
}>;
export declare const SUBSQUID_PAGINATION_LIMIT = 500;
