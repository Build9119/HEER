import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const WhatsAppTemplateLocationParamDetails: core.serialization.ObjectSchema<serializers.WhatsAppTemplateLocationParamDetails.Raw, ElevenLabs.WhatsAppTemplateLocationParamDetails>;
export declare namespace WhatsAppTemplateLocationParamDetails {
    interface Raw {
        latitude: string;
        longitude: string;
        name: string;
        address: string;
    }
}
