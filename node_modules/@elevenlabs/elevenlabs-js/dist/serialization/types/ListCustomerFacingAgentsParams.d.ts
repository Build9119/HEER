import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListCustomerFacingAgentsParams: core.serialization.ObjectSchema<serializers.ListCustomerFacingAgentsParams.Raw, ElevenLabs.ListCustomerFacingAgentsParams>;
export declare namespace ListCustomerFacingAgentsParams {
    interface Raw {
        smb_tool_type?: "list_customer_facing_agents" | null;
    }
}
