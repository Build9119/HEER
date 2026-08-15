import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateBasicAuthRequest: core.serialization.ObjectSchema<serializers.CreateBasicAuthRequest.Raw, ElevenLabs.CreateBasicAuthRequest>;
export declare namespace CreateBasicAuthRequest {
    interface Raw {
        name: string;
        provider: string;
        username: string;
        password: string;
    }
}
