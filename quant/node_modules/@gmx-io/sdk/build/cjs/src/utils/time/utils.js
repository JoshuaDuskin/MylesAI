"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.nowInSeconds = exports.periodToSeconds = exports.secondsToPeriod = exports.secondsFrom = void 0;
const SECONDS_IN_PERIOD = {
    "1m": 60,
    "5m": 60 * 5,
    "15m": 60 * 15,
    "1h": 60 * 60,
    "4h": 60 * 60 * 4,
    "1d": 60 * 60 * 24,
    "1y": 60 * 60 * 24 * 365,
};
function secondsFrom(period) {
    return SECONDS_IN_PERIOD[period];
}
exports.secondsFrom = secondsFrom;
function secondsToPeriod(seconds, period, roundUp = false) {
    const secondsInPeriod = secondsFrom(period);
    const roundedSeconds = roundUp ? Math.ceil(seconds / secondsInPeriod) : Math.floor(seconds / secondsInPeriod);
    return roundedSeconds;
}
exports.secondsToPeriod = secondsToPeriod;
function periodToSeconds(periodsCount, period) {
    return periodsCount * secondsFrom(period);
}
exports.periodToSeconds = periodToSeconds;
function nowInSeconds() {
    return Math.floor(Date.now() / 1000);
}
exports.nowInSeconds = nowInSeconds;
