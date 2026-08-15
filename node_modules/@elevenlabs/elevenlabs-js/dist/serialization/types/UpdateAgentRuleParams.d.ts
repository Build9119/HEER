import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateAgentRuleParams: core.serialization.ObjectSchema<serializers.UpdateAgentRuleParams.Raw, ElevenLabs.UpdateAgentRuleParams>;
export declare namespace UpdateAgentRuleParams {
    interface Raw {
        smb_tool_type?: "update_agent_rule" | null;
    }
}
