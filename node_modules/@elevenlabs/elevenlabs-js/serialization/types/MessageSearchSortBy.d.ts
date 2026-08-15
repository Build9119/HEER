import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const MessageSearchSortBy: core.serialization.Schema<serializers.MessageSearchSortBy.Raw, ElevenLabs.MessageSearchSortBy>;
export declare namespace MessageSearchSortBy {
    type Raw = "search_score" | "created_at";
}
