import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateClientParams: core.serialization.ObjectSchema<serializers.CreateClientParams.Raw, ElevenLabs.CreateClientParams>;
export declare namespace CreateClientParams {
    interface Raw {
        smb_tool_type?: "create_client" | null;
    }
}
