import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { WhatsAppTemplateTextParam } from "./WhatsAppTemplateTextParam";
export declare const WhatsAppTemplateBodyComponentParams: core.serialization.ObjectSchema<serializers.WhatsAppTemplateBodyComponentParams.Raw, ElevenLabs.WhatsAppTemplateBodyComponentParams>;
export declare namespace WhatsAppTemplateBodyComponentParams {
    interface Raw {
        parameters: WhatsAppTemplateTextParam.Raw[];
    }
}
