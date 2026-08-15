import type * as ElevenLabs from "../index";
export interface PendingClipTask {
    type: ElevenLabs.PendingClipTaskType;
    progress?: number;
    startedAtMs?: number;
    updatedAtMs?: number;
    metadata?: Record<string, unknown>;
}
