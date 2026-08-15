import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ToDialogueSettingsResponseModel: core.serialization.ObjectSchema<serializers.ToDialogueSettingsResponseModel.Raw, ElevenLabs.ToDialogueSettingsResponseModel>;
export declare namespace ToDialogueSettingsResponseModel {
    interface Raw {
        stability?: number | null;
        speed?: number | null;
    }
}
