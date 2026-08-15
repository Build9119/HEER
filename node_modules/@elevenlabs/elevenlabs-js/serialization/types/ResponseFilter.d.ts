import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ResponseFilterMode } from "./ResponseFilterMode";
export declare const ResponseFilter: core.serialization.ObjectSchema<serializers.ResponseFilter.Raw, ElevenLabs.ResponseFilter>;
export declare namespace ResponseFilter {
    interface Raw {
        mode?: ResponseFilterMode.Raw | null;
        filters?: string[] | null;
        content_type?: "application/json" | null;
    }
}
