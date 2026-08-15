import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AudioKeyMoment } from "./AudioKeyMoment";
import { AudioSegment } from "./AudioSegment";
export declare const AudioAnalysisResult: core.serialization.ObjectSchema<serializers.AudioAnalysisResult.Raw, ElevenLabs.AudioAnalysisResult>;
export declare namespace AudioAnalysisResult {
    interface Raw {
        title: string;
        description: string;
        content_type?: string | null;
        overall_pacing?: string | null;
        segments?: AudioSegment.Raw[] | null;
        key_moments?: AudioKeyMoment.Raw[] | null;
    }
}
