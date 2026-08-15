import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListAgentRulesParams: core.serialization.ObjectSchema<serializers.ListAgentRulesParams.Raw, ElevenLabs.ListAgentRulesParams>;
export declare namespace ListAgentRulesParams {
    interface Raw {
        smb_tool_type?: "list_agent_rules" | null;
    }
}
