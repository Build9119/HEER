import type * as ElevenLabs from "../../../../../../../api/index";
import * as core from "../../../../../../../core";
import type * as serializers from "../../../../../../index";
import { ConversationInitiationClientDataRequestInput } from "../../../../../../types/ConversationInitiationClientDataRequestInput";
import { TelephonyDirection } from "../../../../../../types/TelephonyDirection";
export declare const BodyRegisterATwilioCallAndReturnTwiMlV1ConvaiTwilioRegisterCallPost: core.serialization.Schema<serializers.conversationalAi.BodyRegisterATwilioCallAndReturnTwiMlV1ConvaiTwilioRegisterCallPost.Raw, ElevenLabs.conversationalAi.BodyRegisterATwilioCallAndReturnTwiMlV1ConvaiTwilioRegisterCallPost>;
export declare namespace BodyRegisterATwilioCallAndReturnTwiMlV1ConvaiTwilioRegisterCallPost {
    interface Raw {
        agent_id: string;
        from_number: string;
        to_number: string;
        direction?: TelephonyDirection.Raw | null;
        conversation_initiation_client_data?: ConversationInitiationClientDataRequestInput.Raw | null;
    }
}
