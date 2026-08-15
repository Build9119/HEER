import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { StudioAgentToolSettingsModel } from "./StudioAgentToolSettingsModel";
export declare const StudioAgentSettingsModel: core.serialization.ObjectSchema<serializers.StudioAgentSettingsModel.Raw, ElevenLabs.StudioAgentSettingsModel>;
export declare namespace StudioAgentSettingsModel {
    interface Raw {
        tool_settings?: Record<string, StudioAgentToolSettingsModel.Raw> | null;
    }
}
