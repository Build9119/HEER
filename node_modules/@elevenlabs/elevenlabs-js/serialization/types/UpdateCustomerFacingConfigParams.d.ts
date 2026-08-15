import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateCustomerFacingConfigParams: core.serialization.ObjectSchema<serializers.UpdateCustomerFacingConfigParams.Raw, ElevenLabs.UpdateCustomerFacingConfigParams>;
export declare namespace UpdateCustomerFacingConfigParams {
    interface Raw {
        smb_tool_type?: "update_customer_facing_config" | null;
    }
}
