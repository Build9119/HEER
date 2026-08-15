import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { CueOptionsRequest } from "./CueOptionsRequest";
import { MediaId } from "./MediaId";
export declare const SubtitleOrderItemRequest: core.serialization.ObjectSchema<serializers.SubtitleOrderItemRequest.Raw, ElevenLabs.SubtitleOrderItemRequest>;
export declare namespace SubtitleOrderItemRequest {
    interface Raw {
        media_ids: MediaId.Raw[];
        source_language: string;
        destination_languages: string[];
        cue_options?: CueOptionsRequest.Raw | null;
        sdh?: boolean | null;
        instructions?: string | null;
    }
}
