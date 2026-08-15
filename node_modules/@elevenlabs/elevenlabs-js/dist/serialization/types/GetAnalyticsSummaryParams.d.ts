import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GetAnalyticsSummaryParams: core.serialization.ObjectSchema<serializers.GetAnalyticsSummaryParams.Raw, ElevenLabs.GetAnalyticsSummaryParams>;
export declare namespace GetAnalyticsSummaryParams {
    interface Raw {
        smb_tool_type?: "get_analytics_summary" | null;
    }
}
