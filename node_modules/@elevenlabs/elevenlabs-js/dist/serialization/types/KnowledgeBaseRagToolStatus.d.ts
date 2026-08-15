import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const KnowledgeBaseRagToolStatus: core.serialization.Schema<serializers.KnowledgeBaseRagToolStatus.Raw, ElevenLabs.KnowledgeBaseRagToolStatus>;
export declare namespace KnowledgeBaseRagToolStatus {
    type Raw = "success" | "no_documents" | "no_results";
}
