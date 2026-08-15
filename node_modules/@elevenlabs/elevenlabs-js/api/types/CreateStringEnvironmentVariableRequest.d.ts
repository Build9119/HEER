export interface CreateStringEnvironmentVariableRequest {
    /** Unique label for the environment variable. */
    label: string;
    /** Environment-specific values. Must include 'production' key. */
    values: Record<string, string>;
}
