import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeChunkSizeExceededErrorPayload: core.serialization.ObjectSchema<serializers.ScribeChunkSizeExceededErrorPayload.Raw, ElevenLabs.ScribeChunkSizeExceededErrorPayload>;
export declare namespace ScribeChunkSizeExceededErrorPayload {
    interface Raw {
        message_type: "chunk_size_exceeded";
        error: string;
    }
}
