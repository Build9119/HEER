import type * as ElevenLabs from "../../../../../../../api/index";
import * as core from "../../../../../../../core";
import type * as serializers from "../../../../../../index";
import { InboundSipTrunkConfigRequestModel } from "../../../../../../types/InboundSipTrunkConfigRequestModel";
import { LivekitStackType } from "../../../../../../types/LivekitStackType";
import { OutboundSipTrunkConfigRequestModel } from "../../../../../../types/OutboundSipTrunkConfigRequestModel";
export declare const UpdatePhoneNumberRequest: core.serialization.Schema<serializers.conversationalAi.UpdatePhoneNumberRequest.Raw, ElevenLabs.conversationalAi.UpdatePhoneNumberRequest>;
export declare namespace UpdatePhoneNumberRequest {
    interface Raw {
        agent_id?: string | null;
        label?: string | null;
        inbound_trunk_config?: InboundSipTrunkConfigRequestModel.Raw | null;
        outbound_trunk_config?: OutboundSipTrunkConfigRequestModel.Raw | null;
        livekit_stack?: LivekitStackType.Raw | null;
        store_sip_messages?: boolean | null;
        environment?: string | null;
        branch_id?: string | null;
    }
}
