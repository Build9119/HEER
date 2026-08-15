import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { WhatsAppTemplateHeaderComponentParamsParametersItem } from "./WhatsAppTemplateHeaderComponentParamsParametersItem";
export declare const WhatsAppTemplateHeaderComponentParams: core.serialization.ObjectSchema<serializers.WhatsAppTemplateHeaderComponentParams.Raw, ElevenLabs.WhatsAppTemplateHeaderComponentParams>;
export declare namespace WhatsAppTemplateHeaderComponentParams {
    interface Raw {
        parameters: WhatsAppTemplateHeaderComponentParamsParametersItem.Raw[];
    }
}
