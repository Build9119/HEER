import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const StudioAgentToolSettingsModel: core.serialization.ObjectSchema<serializers.StudioAgentToolSettingsModel.Raw, ElevenLabs.StudioAgentToolSettingsModel>;
export declare namespace StudioAgentToolSettingsModel {
    interface Raw {
        skip_confirmation?: boolean | null;
    }
}
