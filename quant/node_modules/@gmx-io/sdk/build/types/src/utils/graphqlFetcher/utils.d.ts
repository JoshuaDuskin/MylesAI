export default function graphqlFetcher<T>(endpoint: string, query: string, variables?: object): Promise<T | undefined>;
