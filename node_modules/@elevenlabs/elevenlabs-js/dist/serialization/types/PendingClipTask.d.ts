import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { PendingClipTaskType } from "./PendingClipTaskType";
export declare const PendingClipTask: core.serialization.ObjectSchema<serializers.PendingClipTask.Raw, ElevenLabs.PendingClipTask>;
export declare namespace PendingClipTask {
    interface Raw {
        type: PendingClipTaskType.Raw;
        progress?: number | null;
        started_at_ms?: number | null;
        updated_at_ms?: number | null;
        metadata?: Record<string, unknown> | null;
    }
}
