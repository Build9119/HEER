import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { MediaId } from "./MediaId";
export declare const OrderMediaResponse: core.serialization.ObjectSchema<serializers.OrderMediaResponse.Raw, ElevenLabs.OrderMediaResponse>;
export declare namespace OrderMediaResponse {
    interface Raw {
        media_id: MediaId.Raw;
        name: string;
        content_type: string;
        language?: string | null;
        signed_url: string;
    }
}
