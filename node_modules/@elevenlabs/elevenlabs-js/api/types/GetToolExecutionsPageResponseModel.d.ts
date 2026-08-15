import type * as ElevenLabs from "../index";
export interface GetToolExecutionsPageResponseModel {
    executions: ElevenLabs.ToolExecutionResponseModel[];
    nextCursor?: string;
    hasMore: boolean;
}
