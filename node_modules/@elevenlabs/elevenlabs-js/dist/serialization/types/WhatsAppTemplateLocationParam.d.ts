import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { WhatsAppTemplateLocationParamDetails } from "./WhatsAppTemplateLocationParamDetails";
export declare const WhatsAppTemplateLocationParam: core.serialization.ObjectSchema<serializers.WhatsAppTemplateLocationParam.Raw, ElevenLabs.WhatsAppTemplateLocationParam>;
export declare namespace WhatsAppTemplateLocationParam {
    interface Raw {
        location: WhatsAppTemplateLocationParamDetails.Raw;
    }
}
