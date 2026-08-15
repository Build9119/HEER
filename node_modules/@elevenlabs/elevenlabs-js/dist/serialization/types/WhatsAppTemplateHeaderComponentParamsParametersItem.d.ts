import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { WhatsAppTemplateDocumentParam } from "./WhatsAppTemplateDocumentParam";
import { WhatsAppTemplateImageParam } from "./WhatsAppTemplateImageParam";
import { WhatsAppTemplateLocationParam } from "./WhatsAppTemplateLocationParam";
import { WhatsAppTemplateTextParam } from "./WhatsAppTemplateTextParam";
export declare const WhatsAppTemplateHeaderComponentParamsParametersItem: core.serialization.Schema<serializers.WhatsAppTemplateHeaderComponentParamsParametersItem.Raw, ElevenLabs.WhatsAppTemplateHeaderComponentParamsParametersItem>;
export declare namespace WhatsAppTemplateHeaderComponentParamsParametersItem {
    type Raw = WhatsAppTemplateHeaderComponentParamsParametersItem.Document | WhatsAppTemplateHeaderComponentParamsParametersItem.Image | WhatsAppTemplateHeaderComponentParamsParametersItem.Location | WhatsAppTemplateHeaderComponentParamsParametersItem.Text;
    interface Document extends WhatsAppTemplateDocumentParam.Raw {
        type: "document";
    }
    interface Image extends WhatsAppTemplateImageParam.Raw {
        type: "image";
    }
    interface Location extends WhatsAppTemplateLocationParam.Raw {
        type: "location";
    }
    interface Text extends WhatsAppTemplateTextParam.Raw {
        type: "text";
    }
}
