import type * as ElevenLabs from "../index";
export type UnitTestRunResponseModelTestInfo = ElevenLabs.UnitTestRunResponseModelTestInfo.Llm | ElevenLabs.UnitTestRunResponseModelTestInfo.Simulation | ElevenLabs.UnitTestRunResponseModelTestInfo.Tool;
export declare namespace UnitTestRunResponseModelTestInfo {
    interface Llm extends ElevenLabs.ResponseUnitTestModel {
        type: "llm";
    }
    interface Simulation extends ElevenLabs.SimulationTestModel {
        type: "simulation";
    }
    interface Tool extends ElevenLabs.ToolCallUnitTestModel {
        type: "tool";
    }
}
