import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { WhatsAppTemplateTextParam } from "./WhatsAppTemplateTextParam";
export declare const WhatsAppTemplateButtonComponentParams: core.serialization.ObjectSchema<serializers.WhatsAppTemplateButtonComponentParams.Raw, ElevenLabs.WhatsAppTemplateButtonComponentParams>;
export declare namespace WhatsAppTemplateButtonComponentParams {
    interface Raw {
        parameters: WhatsAppTemplateTextParam.Raw[];
        index: number;
        sub_type: string;
    }
}
