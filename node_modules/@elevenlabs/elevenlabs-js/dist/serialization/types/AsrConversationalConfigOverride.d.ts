import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AsrConversationalConfigOverride: core.serialization.ObjectSchema<serializers.AsrConversationalConfigOverride.Raw, ElevenLabs.AsrConversationalConfigOverride>;
export declare namespace AsrConversationalConfigOverride {
    interface Raw {
        keywords?: string[] | null;
    }
}
