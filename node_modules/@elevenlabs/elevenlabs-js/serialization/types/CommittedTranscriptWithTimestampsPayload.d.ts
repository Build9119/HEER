import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { TranscriptionWord } from "./TranscriptionWord";
export declare const CommittedTranscriptWithTimestampsPayload: core.serialization.ObjectSchema<serializers.CommittedTranscriptWithTimestampsPayload.Raw, ElevenLabs.CommittedTranscriptWithTimestampsPayload>;
export declare namespace CommittedTranscriptWithTimestampsPayload {
    interface Raw {
        message_type: "committed_transcript_with_timestamps";
        text: string;
        language_code?: string | null;
        words?: TranscriptionWord.Raw[] | null;
    }
}
