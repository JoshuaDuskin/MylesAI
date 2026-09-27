export declare class LRUCache<T> {
    private capacity;
    private cache;
    constructor(capacity: number);
    has(key: string): boolean;
    get(key: string): T | undefined;
    set(key: string, value: T): void;
    delete(key: string): void;
    getKeys(): string[];
    clean(): void;
}
