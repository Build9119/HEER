import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { MockingStrategy } from "./MockingStrategy";
import { MockNoMatchBehavior } from "./MockNoMatchBehavior";
export declare const OrchestratorToolMockBehaviorConfig: core.serialization.ObjectSchema<serializers.OrchestratorToolMockBehaviorConfig.Raw, ElevenLabs.OrchestratorToolMockBehaviorConfig>;
export declare namespace OrchestratorToolMockBehaviorConfig {
    interface Raw {
        mocking_strategy?: MockingStrategy.Raw | null;
        fallback_strategy?: MockNoMatchBehavior.Raw | null;
        mocked_tool_names?: string[] | null;
    }
}
