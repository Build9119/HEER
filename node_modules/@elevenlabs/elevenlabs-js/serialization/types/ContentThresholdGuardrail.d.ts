import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ContentThresholdGuardrailThreshold } from "./ContentThresholdGuardrailThreshold";
export declare const ContentThresholdGuardrail: core.serialization.ObjectSchema<serializers.ContentThresholdGuardrail.Raw, ElevenLabs.ContentThresholdGuardrail>;
export declare namespace ContentThresholdGuardrail {
    interface Raw {
        is_enabled?: boolean | null;
        threshold?: ContentThresholdGuardrailThreshold.Raw | null;
    }
}
