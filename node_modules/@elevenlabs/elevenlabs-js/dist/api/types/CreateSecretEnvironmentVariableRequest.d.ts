import type * as ElevenLabs from "../index";
export interface CreateSecretEnvironmentVariableRequest {
    /** Unique label for the environment variable. */
    label: string;
    /** Environment-specific secret references. Must include 'production' key. */
    values: Record<string, ElevenLabs.EnvironmentVariableSecretValueRequest>;
}
