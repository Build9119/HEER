import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SfxSourceContext: core.serialization.ObjectSchema<serializers.SfxSourceContext.Raw, ElevenLabs.SfxSourceContext>;
export declare namespace SfxSourceContext {
    interface Raw {
        sound_generation_history_item_id?: string | null;
        text?: string | null;
        generation_config?: Record<string, unknown> | null;
    }
}
