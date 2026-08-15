import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AutoSyncInfo: core.serialization.ObjectSchema<serializers.AutoSyncInfo.Raw, ElevenLabs.AutoSyncInfo>;
export declare namespace AutoSyncInfo {
    interface Raw {
        minimum_frequency_days?: number | null;
        auto_remove?: boolean | null;
        consec_failures?: number | null;
        next_refresh_by?: number | null;
    }
}
