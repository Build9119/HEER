import type * as ElevenLabs from "../../../../../../../api/index";
import * as core from "../../../../../../../core";
import type * as serializers from "../../../../../../index";
import { AgentPlatformSettingsRequestModel } from "../../../../../../types/AgentPlatformSettingsRequestModel";
import { AgentWorkflowRequestModel } from "../../../../../../types/AgentWorkflowRequestModel";
import { ConversationalConfig } from "../../../../../../types/ConversationalConfig";
export declare const UpdateAgentRequest: core.serialization.Schema<serializers.conversationalAi.UpdateAgentRequest.Raw, Omit<ElevenLabs.conversationalAi.UpdateAgentRequest, "enableVersioningIfNotEnabled" | "branchId">>;
export declare namespace UpdateAgentRequest {
    interface Raw {
        conversation_config?: ConversationalConfig.Raw | null;
        platform_settings?: AgentPlatformSettingsRequestModel.Raw | null;
        workflow?: AgentWorkflowRequestModel.Raw | null;
        name?: string | null;
        tags?: string[] | null;
        version_description?: string | null;
    }
}
