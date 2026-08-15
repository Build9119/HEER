import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AnalysisPropertyType: core.serialization.Schema<serializers.AnalysisPropertyType.Raw, ElevenLabs.AnalysisPropertyType>;
export declare namespace AnalysisPropertyType {
    type Raw = "boolean" | "string" | "integer" | "number";
}
