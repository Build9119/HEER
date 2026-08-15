import type * as ElevenLabs from "../../../../../../../../api/index";
import * as core from "../../../../../../../../core";
import type * as serializers from "../../../../../../../index";
export declare const MessagesTextSearchRequestSummaryMode: core.serialization.Schema<serializers.conversationalAi.conversations.MessagesTextSearchRequestSummaryMode.Raw, ElevenLabs.conversationalAi.conversations.MessagesTextSearchRequestSummaryMode>;
export declare namespace MessagesTextSearchRequestSummaryMode {
    type Raw = "exclude" | "include";
}
