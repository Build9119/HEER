import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AsrConversationalConfigOverrideConfig: core.serialization.ObjectSchema<serializers.AsrConversationalConfigOverrideConfig.Raw, ElevenLabs.AsrConversationalConfigOverrideConfig>;
export declare namespace AsrConversationalConfigOverrideConfig {
    interface Raw {
        keywords?: boolean | null;
    }
}
