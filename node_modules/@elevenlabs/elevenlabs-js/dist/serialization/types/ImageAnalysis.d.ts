import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ImageAnalysisResult } from "./ImageAnalysisResult";
import { ImageAnalysisStatus } from "./ImageAnalysisStatus";
export declare const ImageAnalysis: core.serialization.ObjectSchema<serializers.ImageAnalysis.Raw, ElevenLabs.ImageAnalysis>;
export declare namespace ImageAnalysis {
    interface Raw {
        status: ImageAnalysisStatus.Raw;
        data?: ImageAnalysisResult.Raw | null;
        updated_at_ms?: number | null;
    }
}
