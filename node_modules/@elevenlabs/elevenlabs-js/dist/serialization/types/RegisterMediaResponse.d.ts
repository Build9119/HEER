import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { MediaId } from "./MediaId";
export declare const RegisterMediaResponse: core.serialization.ObjectSchema<serializers.RegisterMediaResponse.Raw, ElevenLabs.RegisterMediaResponse>;
export declare namespace RegisterMediaResponse {
    interface Raw {
        media_id: MediaId.Raw;
    }
}
