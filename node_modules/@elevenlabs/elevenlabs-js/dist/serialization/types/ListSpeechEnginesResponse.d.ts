import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { SpeechEngineSummaryResponse } from "./SpeechEngineSummaryResponse";
export declare const ListSpeechEnginesResponse: core.serialization.ObjectSchema<serializers.ListSpeechEnginesResponse.Raw, ElevenLabs.ListSpeechEnginesResponse>;
export declare namespace ListSpeechEnginesResponse {
    interface Raw {
        speech_engines: SpeechEngineSummaryResponse.Raw[];
        next_cursor?: string | null;
        has_more: boolean;
    }
}
