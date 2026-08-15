import type * as ElevenLabs from "../index";
export type WhatsAppTemplateHeaderComponentParamsParametersItem = ElevenLabs.WhatsAppTemplateHeaderComponentParamsParametersItem.Document | ElevenLabs.WhatsAppTemplateHeaderComponentParamsParametersItem.Image | ElevenLabs.WhatsAppTemplateHeaderComponentParamsParametersItem.Location | ElevenLabs.WhatsAppTemplateHeaderComponentParamsParametersItem.Text;
export declare namespace WhatsAppTemplateHeaderComponentParamsParametersItem {
    interface Document extends ElevenLabs.WhatsAppTemplateDocumentParam {
        type: "document";
    }
    interface Image extends ElevenLabs.WhatsAppTemplateImageParam {
        type: "image";
    }
    interface Location extends ElevenLabs.WhatsAppTemplateLocationParam {
        type: "location";
    }
    interface Text extends ElevenLabs.WhatsAppTemplateTextParam {
        type: "text";
    }
}
