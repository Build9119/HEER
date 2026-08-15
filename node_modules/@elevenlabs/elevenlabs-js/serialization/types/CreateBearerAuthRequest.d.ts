import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateBearerAuthRequest: core.serialization.ObjectSchema<serializers.CreateBearerAuthRequest.Raw, ElevenLabs.CreateBearerAuthRequest>;
export declare namespace CreateBearerAuthRequest {
    interface Raw {
        name: string;
        provider: string;
        token: string;
    }
}
