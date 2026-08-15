import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AgentConfigOverrideConfig } from "./AgentConfigOverrideConfig";
import { AsrConversationalConfigOverrideConfig } from "./AsrConversationalConfigOverrideConfig";
import { ConversationConfigOverrideConfig } from "./ConversationConfigOverrideConfig";
import { TtsConversationalConfigOverrideConfig } from "./TtsConversationalConfigOverrideConfig";
import { TurnConfigOverrideConfig } from "./TurnConfigOverrideConfig";
export declare const ConversationConfigClientOverrideConfigOutput: core.serialization.ObjectSchema<serializers.ConversationConfigClientOverrideConfigOutput.Raw, ElevenLabs.ConversationConfigClientOverrideConfigOutput>;
export declare namespace ConversationConfigClientOverrideConfigOutput {
    interface Raw {
        asr?: AsrConversationalConfigOverrideConfig.Raw | null;
        turn?: TurnConfigOverrideConfig.Raw | null;
        tts?: TtsConversationalConfigOverrideConfig.Raw | null;
        conversation?: ConversationConfigOverrideConfig.Raw | null;
        agent?: AgentConfigOverrideConfig.Raw | null;
    }
}
