import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ManualSource: core.serialization.ObjectSchema<serializers.ManualSource.Raw, ElevenLabs.ManualSource>;
export declare namespace ManualSource {
    interface Raw {
        type?: "manual" | null;
        created_by_user_id: string;
        notes?: string | null;
    }
}
