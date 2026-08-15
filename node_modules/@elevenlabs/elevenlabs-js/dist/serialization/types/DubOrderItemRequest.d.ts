import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { MediaId } from "./MediaId";
export declare const DubOrderItemRequest: core.serialization.ObjectSchema<serializers.DubOrderItemRequest.Raw, ElevenLabs.DubOrderItemRequest>;
export declare namespace DubOrderItemRequest {
    interface Raw {
        media_id: MediaId.Raw;
        source_language: string;
        destination_languages: string[];
        include_captions: boolean;
        include_source_captions: boolean;
        instructions?: string | null;
        captions_sdh?: boolean | null;
    }
}
