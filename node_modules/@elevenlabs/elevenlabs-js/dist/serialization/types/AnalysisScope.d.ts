import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AnalysisScope: core.serialization.Schema<serializers.AnalysisScope.Raw, ElevenLabs.AnalysisScope>;
export declare namespace AnalysisScope {
    type Raw = "conversation" | "agent";
}
