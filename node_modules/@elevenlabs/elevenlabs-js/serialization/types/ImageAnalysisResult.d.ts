import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ImageSubject } from "./ImageSubject";
export declare const ImageAnalysisResult: core.serialization.ObjectSchema<serializers.ImageAnalysisResult.Raw, ElevenLabs.ImageAnalysisResult>;
export declare namespace ImageAnalysisResult {
    interface Raw {
        title: string;
        description: string;
        content_type?: string | null;
        mood_and_style?: string | null;
        composition_notes?: string | null;
        visible_text?: string | null;
        subjects?: ImageSubject.Raw[] | null;
    }
}
