import type * as ElevenLabs from "../index";
export interface EnvironmentVariablesListResponse {
    environmentVariables: ElevenLabs.EnvironmentVariableResponse[];
    nextCursor?: string;
    hasMore: boolean;
}
