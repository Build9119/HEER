import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { WhatsAppTemplateDocumentParamDetails } from "./WhatsAppTemplateDocumentParamDetails";
export declare const WhatsAppTemplateDocumentParam: core.serialization.ObjectSchema<serializers.WhatsAppTemplateDocumentParam.Raw, ElevenLabs.WhatsAppTemplateDocumentParam>;
export declare namespace WhatsAppTemplateDocumentParam {
    interface Raw {
        document: WhatsAppTemplateDocumentParamDetails.Raw;
    }
}
