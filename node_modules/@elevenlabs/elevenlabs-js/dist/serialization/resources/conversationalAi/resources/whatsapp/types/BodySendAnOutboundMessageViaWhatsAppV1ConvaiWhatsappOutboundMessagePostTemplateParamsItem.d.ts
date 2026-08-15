import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
import { WhatsAppTemplateBodyComponentParams } from "../../../../../types/WhatsAppTemplateBodyComponentParams";
import { WhatsAppTemplateButtonComponentParams } from "../../../../../types/WhatsAppTemplateButtonComponentParams";
import { WhatsAppTemplateHeaderComponentParams } from "../../../../../types/WhatsAppTemplateHeaderComponentParams";
export declare const BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem: core.serialization.Schema<serializers.conversationalAi.BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem.Raw, ElevenLabs.conversationalAi.BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem>;
export declare namespace BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem {
    type Raw = BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem.Body | BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem.Button | BodySendAnOutboundMessageViaWhatsAppV1ConvaiWhatsappOutboundMessagePostTemplateParamsItem.Header;
    interface Body extends WhatsAppTemplateBodyComponentParams.Raw {
        type: "body";
    }
    interface Button extends WhatsAppTemplateButtonComponentParams.Raw {
        type: "button";
    }
    interface Header extends WhatsAppTemplateHeaderComponentParams.Raw {
        type: "header";
    }
}
