import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CommittedTranscriptPayload: core.serialization.ObjectSchema<serializers.CommittedTranscriptPayload.Raw, ElevenLabs.CommittedTranscriptPayload>;
export declare namespace CommittedTranscriptPayload {
    interface Raw {
        message_type: "committed_transcript";
        text: string;
    }
}
