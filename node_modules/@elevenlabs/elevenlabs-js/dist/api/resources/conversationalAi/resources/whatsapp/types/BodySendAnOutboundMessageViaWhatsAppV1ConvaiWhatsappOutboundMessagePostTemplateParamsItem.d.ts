import type * as ElevenLabs from "../../../../../index";
export type BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem = ElevenLabs.conversationalAi.BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem.Body | ElevenLabs.conversationalAi.BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem.Button | ElevenLabs.conversationalAi.BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem.Header;
export declare namespace BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem {
    interface Body extends ElevenLabs.WhatsAppTemplateBodyComponentParams {
        type: "body";
    }
    interface Button extends ElevenLabs.WhatsAppTemplateButtonComponentParams {
        type: "button";
    }
    interface Header extends ElevenLabs.WhatsAppTemplateHeaderComponentParams {
        type: "header";
    }
}
