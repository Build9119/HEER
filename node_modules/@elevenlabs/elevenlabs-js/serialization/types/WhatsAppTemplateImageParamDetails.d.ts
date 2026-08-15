import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const WhatsAppTemplateImageParamDetails: core.serialization.ObjectSchema<serializers.WhatsAppTemplateImageParamDetails.Raw, ElevenLabs.WhatsAppTemplateImageParamDetails>;
export declare namespace WhatsAppTemplateImageParamDetails {
    interface Raw {
        link: string;
    }
}
