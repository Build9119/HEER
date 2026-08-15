import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const WhatsAppTemplateTextParam: core.serialization.ObjectSchema<serializers.WhatsAppTemplateTextParam.Raw, ElevenLabs.WhatsAppTemplateTextParam>;
export declare namespace WhatsAppTemplateTextParam {
    interface Raw {
        parameter_name?: string | null;
        type?: "text" | null;
        text: string;
    }
}
