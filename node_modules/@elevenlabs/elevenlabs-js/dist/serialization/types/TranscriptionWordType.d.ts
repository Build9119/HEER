import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TranscriptionWordType: core.serialization.Schema<serializers.TranscriptionWordType.Raw, ElevenLabs.TranscriptionWordType>;
export declare namespace TranscriptionWordType {
    type Raw = "word" | "spacing";
}
