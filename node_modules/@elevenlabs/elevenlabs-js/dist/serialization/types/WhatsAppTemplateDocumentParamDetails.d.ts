import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const WhatsAppTemplateDocumentParamDetails: core.serialization.ObjectSchema<serializers.WhatsAppTemplateDocumentParamDetails.Raw, ElevenLabs.WhatsAppTemplateDocumentParamDetails>;
export declare namespace WhatsAppTemplateDocumentParamDetails {
    interface Raw {
        link: string;
        filename?: string | null;
    }
}
