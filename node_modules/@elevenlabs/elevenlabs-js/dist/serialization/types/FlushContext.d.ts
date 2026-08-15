import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const FlushContext: core.serialization.ObjectSchema<serializers.FlushContext.Raw, ElevenLabs.FlushContext>;
export declare namespace FlushContext {
    interface Raw {
        context_id: string;
        text?: string | null;
        flush: boolean;
    }
}
