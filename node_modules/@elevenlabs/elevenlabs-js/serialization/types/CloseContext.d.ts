import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CloseContext: core.serialization.ObjectSchema<serializers.CloseContext.Raw, ElevenLabs.CloseContext>;
export declare namespace CloseContext {
    interface Raw {
        context_id: string;
        close_context: boolean;
    }
}
