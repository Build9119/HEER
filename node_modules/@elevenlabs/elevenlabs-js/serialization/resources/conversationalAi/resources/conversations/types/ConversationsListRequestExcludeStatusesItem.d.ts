import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
export declare const ConversationsListRequestExcludeStatusesItem: core.serialization.Schema<serializers.conversationalAi.ConversationsListRequestExcludeStatusesItem.Raw, ElevenLabs.conversationalAi.ConversationsListRequestExcludeStatusesItem>;
export declare namespace ConversationsListRequestExcludeStatusesItem {
    type Raw = "initiated" | "in-progress" | "processing" | "done" | "failed";
}
