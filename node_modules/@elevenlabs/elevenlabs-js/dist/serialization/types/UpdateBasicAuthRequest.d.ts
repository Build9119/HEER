import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateBasicAuthRequest: core.serialization.ObjectSchema<serializers.UpdateBasicAuthRequest.Raw, ElevenLabs.UpdateBasicAuthRequest>;
export declare namespace UpdateBasicAuthRequest {
    interface Raw {
        provider?: string | null;
        username?: string | null;
        password?: string | null;
    }
}
