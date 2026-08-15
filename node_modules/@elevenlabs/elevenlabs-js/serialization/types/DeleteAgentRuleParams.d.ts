import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteAgentRuleParams: core.serialization.ObjectSchema<serializers.DeleteAgentRuleParams.Raw, ElevenLabs.DeleteAgentRuleParams>;
export declare namespace DeleteAgentRuleParams {
    interface Raw {
        smb_tool_type?: "delete_agent_rule" | null;
    }
}
