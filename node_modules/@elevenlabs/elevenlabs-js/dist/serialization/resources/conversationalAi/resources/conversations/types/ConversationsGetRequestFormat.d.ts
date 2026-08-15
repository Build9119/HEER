import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
export declare const ConversationsGetRequestFormat: core.serialization.Schema<serializers.conversationalAi.ConversationsGetRequestFormat.Raw, ElevenLabs.conversationalAi.ConversationsGetRequestFormat>;
export declare namespace ConversationsGetRequestFormat {
    type Raw = "json" | "opentelemetry";
}
