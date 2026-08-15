import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ListResponseMeta } from "./ListResponseMeta";
import { MessagesSearchResult } from "./MessagesSearchResult";
export declare const MessagesSearchResponse: core.serialization.ObjectSchema<serializers.MessagesSearchResponse.Raw, ElevenLabs.MessagesSearchResponse>;
export declare namespace MessagesSearchResponse {
    interface Raw {
        meta?: ListResponseMeta.Raw | null;
        results: MessagesSearchResult.Raw[];
        next_cursor?: string | null;
        has_more: boolean;
    }
}
