import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ContextualUpdateInfo: core.serialization.ObjectSchema<serializers.ContextualUpdateInfo.Raw, ElevenLabs.ContextualUpdateInfo>;
export declare namespace ContextualUpdateInfo {
    interface Raw {
        context_id: string;
        is_superseded?: boolean | null;
    }
}
