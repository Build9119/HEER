import type * as ElevenLabs from "../../../../../index";
export type TestsUpdateResponse = ElevenLabs.conversationalAi.TestsUpdateResponse.Llm | ElevenLabs.conversationalAi.TestsUpdateResponse.Tool | ElevenLabs.conversationalAi.TestsUpdateResponse.Simulation;
export declare namespace TestsUpdateResponse {
    interface Llm extends ElevenLabs.GetResponseUnitTestResponseModel {
        type: "llm";
    }
    interface Tool extends ElevenLabs.GetToolCallUnitTestResponseModel {
        type: "tool";
    }
    interface Simulation extends ElevenLabs.GetSimulationTestResponseModel {
        type: "simulation";
    }
}
