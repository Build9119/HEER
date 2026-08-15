import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GetClientByPhoneParams: core.serialization.ObjectSchema<serializers.GetClientByPhoneParams.Raw, ElevenLabs.GetClientByPhoneParams>;
export declare namespace GetClientByPhoneParams {
    interface Raw {
        smb_tool_type?: "get_client_by_phone" | null;
    }
}
