import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PartialTranscriptPayload: core.serialization.ObjectSchema<serializers.PartialTranscriptPayload.Raw, ElevenLabs.PartialTranscriptPayload>;
export declare namespace PartialTranscriptPayload {
    interface Raw {
        message_type: "partial_transcript";
        text: string;
    }
}
