import type * as ElevenLabs from "../../../../../../../api/index";
import * as core from "../../../../../../../core";
import type * as serializers from "../../../../../../index";
import { ConversationInitiationClientDataRequestInput } from "../../../../../../types/ConversationInitiationClientDataRequestInput";
import { BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem } from "../../types/BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem";
export declare const BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePost: core.serialization.Schema<serializers.conversationalAi.BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePost.Raw, ElevenLabs.conversationalAi.BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePost>;
export declare namespace BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePost {
    interface Raw {
        whatsapp_phone_number_id: string;
        whatsapp_user_id: string;
        template_name: string;
        template_language_code: string;
        template_params: BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem.Raw[];
        agent_id: string;
        conversation_initiation_client_data?: ConversationInitiationClientDataRequestInput.Raw | null;
    }
}
