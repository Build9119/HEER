import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateCustomHeaderAuthRequest: core.serialization.ObjectSchema<serializers.CreateCustomHeaderAuthRequest.Raw, ElevenLabs.CreateCustomHeaderAuthRequest>;
export declare namespace CreateCustomHeaderAuthRequest {
    interface Raw {
        name: string;
        provider: string;
        header_name: string;
        token: string;
    }
}
