declare const SECONDS_IN_PERIOD: {
    "1m": number;
    "5m": number;
    "15m": number;
    "1h": number;
    "4h": number;
    "1d": number;
    "1y": number;
};
export declare function secondsFrom(period: keyof typeof SECONDS_IN_PERIOD): number;
export declare function secondsToPeriod(seconds: number, period: keyof typeof SECONDS_IN_PERIOD, roundUp?: boolean): number;
export declare function periodToSeconds(periodsCount: number, period: keyof typeof SECONDS_IN_PERIOD): number;
export declare function nowInSeconds(): number;
export {};
