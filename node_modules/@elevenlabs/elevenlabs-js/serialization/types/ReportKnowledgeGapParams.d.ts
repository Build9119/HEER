import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ReportKnowledgeGapParams: core.serialization.ObjectSchema<serializers.ReportKnowledgeGapParams.Raw, ElevenLabs.ReportKnowledgeGapParams>;
export declare namespace ReportKnowledgeGapParams {
    interface Raw {
        smb_tool_type?: "report_knowledge_gap" | null;
    }
}
