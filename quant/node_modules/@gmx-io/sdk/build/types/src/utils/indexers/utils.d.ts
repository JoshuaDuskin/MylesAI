export type GraphQlFilters = {
    OR: GraphQlFilters[];
} | {
    AND: GraphQlFilters[];
} | {
    /**
     * `or` must be a single key-value pair in the object.
     */
    OR?: never;
    /**
     * `and` must be a single key-value pair in the object.
     */
    AND?: never;
    /**
     * Key must not start with an `_`. If you want to use nested filtering add `_` to the parent key itself if possible.
     * Otherwise, if for some reason the field name itself starts with an `_`, change these types.
     */
    [key: `_${string}`]: never;
    [key: string]: string | number | boolean | undefined | GraphQlFilters | string[] | number[] | GraphQlFilters[] | null;
};
export declare function buildFiltersBody(filters: GraphQlFilters, options?: {
    enums?: Record<string, string>;
}): string;
export declare function queryPaginated<T>(fetcher: (limit: number, offset: number) => Promise<T[]>, limit?: number): Promise<T[]>;
