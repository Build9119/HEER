import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateAgentRuleParams: core.serialization.ObjectSchema<serializers.CreateAgentRuleParams.Raw, ElevenLabs.CreateAgentRuleParams>;
export declare namespace CreateAgentRuleParams {
    interface Raw {
        smb_tool_type?: "create_agent_rule" | null;
    }
}
