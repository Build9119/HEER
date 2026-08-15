import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { CreatePrivateKeyJwtRequestAlgorithm } from "./CreatePrivateKeyJwtRequestAlgorithm";
export declare const CreatePrivateKeyJwtRequest: core.serialization.ObjectSchema<serializers.CreatePrivateKeyJwtRequest.Raw, ElevenLabs.CreatePrivateKeyJwtRequest>;
export declare namespace CreatePrivateKeyJwtRequest {
    interface Raw {
        name: string;
        provider: string;
        algorithm?: CreatePrivateKeyJwtRequestAlgorithm.Raw | null;
        key_id?: string | null;
        issuer: string;
        audience: string;
        subject: string;
        expiration_seconds?: number | null;
        extra_params?: Record<string, string> | null;
        secret_key: string;
    }
}
