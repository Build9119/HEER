import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { WhatsAppTemplateImageParamDetails } from "./WhatsAppTemplateImageParamDetails";
export declare const WhatsAppTemplateImageParam: core.serialization.ObjectSchema<serializers.WhatsAppTemplateImageParam.Raw, ElevenLabs.WhatsAppTemplateImageParam>;
export declare namespace WhatsAppTemplateImageParam {
    interface Raw {
        image: WhatsAppTemplateImageParamDetails.Raw;
    }
}
