import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ContentThresholdGuardrailThreshold: core.serialization.Schema<serializers.ContentThresholdGuardrailThreshold.Raw, ElevenLabs.ContentThresholdGuardrailThreshold>;
export declare namespace ContentThresholdGuardrailThreshold {
    type Raw = number | "low" | "medium" | "high";
}
