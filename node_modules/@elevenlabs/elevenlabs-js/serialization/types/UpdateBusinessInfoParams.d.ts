import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateBusinessInfoParams: core.serialization.ObjectSchema<serializers.UpdateBusinessInfoParams.Raw, ElevenLabs.UpdateBusinessInfoParams>;
export declare namespace UpdateBusinessInfoParams {
    interface Raw {
        smb_tool_type?: "update_business_info" | null;
    }
}
