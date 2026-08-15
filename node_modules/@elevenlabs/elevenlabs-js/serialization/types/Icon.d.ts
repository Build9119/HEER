import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const Icon: core.serialization.ObjectSchema<serializers.Icon.Raw, ElevenLabs.Icon>;
export declare namespace Icon {
    interface Raw {
        src: string;
        mimeType?: string | null;
        sizes?: string[] | null;
        [key: string]: any;
    }
}
