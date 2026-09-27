export declare const ZERO_DATA = "0x";
export declare function hashData(dataTypes: string[], dataValues: (string | number | bigint | boolean)[]): string;
export declare function hashString(string: string): string;
export declare function hashDataMap<R extends Record<string, [dataTypes: string[], dataValues: (string | number | bigint | boolean)[]] | undefined>>(map: R): {
    [K in keyof R]: string;
};
export declare function keccakString(string: string): string;
