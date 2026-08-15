import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { KnowledgeBaseLocator } from "./KnowledgeBaseLocator";
import { Llm } from "./Llm";
export declare const PromptAgentApiModelOverrideInput: core.serialization.ObjectSchema<serializers.PromptAgentApiModelOverrideInput.Raw, ElevenLabs.PromptAgentApiModelOverrideInput>;
export declare namespace PromptAgentApiModelOverrideInput {
    interface Raw {
        prompt?: string | null;
        llm?: Llm.Raw | null;
        tool_ids?: string[] | null;
        native_mcp_server_ids?: string[] | null;
        knowledge_base?: KnowledgeBaseLocator.Raw[] | null;
    }
}
