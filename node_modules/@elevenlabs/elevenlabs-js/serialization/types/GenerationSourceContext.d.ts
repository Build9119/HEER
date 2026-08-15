import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ReferenceVideo } from "./ReferenceVideo";
export declare const GenerationSourceContext: core.serialization.ObjectSchema<serializers.GenerationSourceContext.Raw, ElevenLabs.GenerationSourceContext>;
export declare namespace GenerationSourceContext {
    interface Raw {
        source_type?: "generation" | null;
        generation_id: string;
        prompt?: string | null;
        model_id: string;
        model_provider?: string | null;
        generation_session_id?: string | null;
        session_iteration_id?: string | null;
        model_parameters?: Record<string, unknown> | null;
        extend_video?: ReferenceVideo.Raw | null;
    }
}
