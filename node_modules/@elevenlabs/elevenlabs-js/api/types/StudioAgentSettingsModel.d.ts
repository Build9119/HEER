import type * as ElevenLabs from "../index";
export interface StudioAgentSettingsModel {
    toolSettings?: Record<string, ElevenLabs.StudioAgentToolSettingsModel>;
}
