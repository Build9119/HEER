import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ConversationSource: core.serialization.ObjectSchema<serializers.ConversationSource.Raw, ElevenLabs.ConversationSource>;
export declare namespace ConversationSource {
    interface Raw {
        type?: "conversation" | null;
        conversation_id: string;
    }
}
