import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { VideoKeyMoment } from "./VideoKeyMoment";
import { VideoSegment } from "./VideoSegment";
import { VideoSubject } from "./VideoSubject";
export declare const VideoAnalysisResult: core.serialization.ObjectSchema<serializers.VideoAnalysisResult.Raw, ElevenLabs.VideoAnalysisResult>;
export declare namespace VideoAnalysisResult {
    interface Raw {
        title: string;
        description: string;
        content_type?: string | null;
        overall_pacing?: string | null;
        subjects?: VideoSubject.Raw[] | null;
        segments?: VideoSegment.Raw[] | null;
        key_moments?: VideoKeyMoment.Raw[] | null;
    }
}
