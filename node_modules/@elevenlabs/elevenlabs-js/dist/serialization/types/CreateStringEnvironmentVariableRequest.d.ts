import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateStringEnvironmentVariableRequest: core.serialization.ObjectSchema<serializers.CreateStringEnvironmentVariableRequest.Raw, ElevenLabs.CreateStringEnvironmentVariableRequest>;
export declare namespace CreateStringEnvironmentVariableRequest {
    interface Raw {
        label: string;
        values: Record<string, string>;
    }
}
