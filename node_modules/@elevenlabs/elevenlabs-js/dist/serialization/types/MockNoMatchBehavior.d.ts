import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const MockNoMatchBehavior: core.serialization.Schema<serializers.MockNoMatchBehavior.Raw, ElevenLabs.MockNoMatchBehavior>;
export declare namespace MockNoMatchBehavior {
    type Raw = "call_real_tool" | "raise_error";
}
