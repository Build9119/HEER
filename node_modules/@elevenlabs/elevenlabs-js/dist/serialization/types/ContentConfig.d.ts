import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ContentThresholdGuardrail } from "./ContentThresholdGuardrail";
export declare const ContentConfig: core.serialization.ObjectSchema<serializers.ContentConfig.Raw, ElevenLabs.ContentConfig>;
export declare namespace ContentConfig {
    interface Raw {
        sexual?: ContentThresholdGuardrail.Raw | null;
        violence?: ContentThresholdGuardrail.Raw | null;
        harassment?: ContentThresholdGuardrail.Raw | null;
        self_harm?: ContentThresholdGuardrail.Raw | null;
        profanity?: ContentThresholdGuardrail.Raw | null;
        religion_or_politics?: ContentThresholdGuardrail.Raw | null;
        medical_and_legal_information?: ContentThresholdGuardrail.Raw | null;
    }
}
