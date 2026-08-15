import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeliverableInfo: core.serialization.ObjectSchema<serializers.DeliverableInfo.Raw, ElevenLabs.DeliverableInfo>;
export declare namespace DeliverableInfo {
    interface Raw {
        signed_url: string;
        content_type: string;
        name: string;
        version?: number | null;
    }
}
