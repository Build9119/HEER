import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GuardrailExecutionMode: core.serialization.Schema<serializers.GuardrailExecutionMode.Raw, ElevenLabs.GuardrailExecutionMode>;
export declare namespace GuardrailExecutionMode {
    type Raw = "streaming" | "blocking";
}
