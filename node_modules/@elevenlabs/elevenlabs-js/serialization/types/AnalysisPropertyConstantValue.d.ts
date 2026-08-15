import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AnalysisPropertyConstantValue: core.serialization.Schema<serializers.AnalysisPropertyConstantValue.Raw, ElevenLabs.AnalysisPropertyConstantValue>;
export declare namespace AnalysisPropertyConstantValue {
    type Raw = string | number | number | boolean;
}
