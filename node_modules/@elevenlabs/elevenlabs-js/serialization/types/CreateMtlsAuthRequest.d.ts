import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateMtlsAuthRequest: core.serialization.ObjectSchema<serializers.CreateMtlsAuthRequest.Raw, ElevenLabs.CreateMtlsAuthRequest>;
export declare namespace CreateMtlsAuthRequest {
    interface Raw {
        name: string;
        provider: string;
        client_certificate: string;
        client_key: string;
        ca_certificate?: string | null;
        key_passphrase?: string | null;
    }
}
