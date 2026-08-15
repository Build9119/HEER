import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const LanguageInfo: core.serialization.ObjectSchema<serializers.LanguageInfo.Raw, ElevenLabs.LanguageInfo>;
export declare namespace LanguageInfo {
    interface Raw {
        code: string;
        label: string;
    }
}
