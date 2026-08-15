import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const WhatsAppOutboundMessageResponse: core.serialization.ObjectSchema<serializers.WhatsAppOutboundMessageResponse.Raw, ElevenLabs.WhatsAppOutboundMessageResponse>;
export declare namespace WhatsAppOutboundMessageResponse {
    interface Raw {
        conversation_id: string;
    }
}
