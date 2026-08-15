import type * as ElevenLabs from "../../../../../api/index";
import * as core from "../../../../../core";
import type * as serializers from "../../../../index";
import { UpdateEnvironmentVariableRequestValuesValue } from "../../types/UpdateEnvironmentVariableRequestValuesValue";
export declare const UpdateEnvironmentVariableRequest: core.serialization.Schema<serializers.UpdateEnvironmentVariableRequest.Raw, ElevenLabs.UpdateEnvironmentVariableRequest>;
export declare namespace UpdateEnvironmentVariableRequest {
    interface Raw {
        values: Record<string, UpdateEnvironmentVariableRequestValuesValue.Raw | null | undefined>;
    }
}
