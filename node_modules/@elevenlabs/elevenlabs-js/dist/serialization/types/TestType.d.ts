import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TestType: core.serialization.Schema<serializers.TestType.Raw, ElevenLabs.TestType>;
export declare namespace TestType {
    type Raw = "llm" | "tool" | "simulation" | "folder";
}
