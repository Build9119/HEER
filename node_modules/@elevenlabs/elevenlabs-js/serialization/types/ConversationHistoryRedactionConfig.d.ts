import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConfigEntityType } from "./ConfigEntityType";
export declare const ConversationHistoryRedactionConfig: core.serialization.ObjectSchema<serializers.ConversationHistoryRedactionConfig.Raw, ElevenLabs.ConversationHistoryRedactionConfig>;
export declare namespace ConversationHistoryRedactionConfig {
    interface Raw {
        enabled?: boolean | null;
        entities?: ConfigEntityType.Raw[] | null;
    }
}
