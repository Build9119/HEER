import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PromptAgentApiModelOverrideConfig: core.serialization.ObjectSchema<serializers.PromptAgentApiModelOverrideConfig.Raw, ElevenLabs.PromptAgentApiModelOverrideConfig>;
export declare namespace PromptAgentApiModelOverrideConfig {
    interface Raw {
        prompt?: boolean | null;
        llm?: boolean | null;
        tool_ids?: boolean | null;
        native_mcp_server_ids?: boolean | null;
        knowledge_base?: boolean | null;
    }
}
