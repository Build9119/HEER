import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { MockingStrategy } from "./MockingStrategy";
import { MockNoMatchBehavior } from "./MockNoMatchBehavior";
export declare const SimulationToolMockBehaviorConfig: core.serialization.ObjectSchema<serializers.SimulationToolMockBehaviorConfig.Raw, ElevenLabs.SimulationToolMockBehaviorConfig>;
export declare namespace SimulationToolMockBehaviorConfig {
    interface Raw {
        mocking_strategy?: MockingStrategy.Raw | null;
        fallback_strategy?: MockNoMatchBehavior.Raw | null;
        mocked_tool_ids?: string[] | null;
    }
}
