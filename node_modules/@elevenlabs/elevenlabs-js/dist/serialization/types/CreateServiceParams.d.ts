import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateServiceParams: core.serialization.ObjectSchema<serializers.CreateServiceParams.Raw, ElevenLabs.CreateServiceParams>;
export declare namespace CreateServiceParams {
    interface Raw {
        smb_tool_type?: "create_service" | null;
    }
}
