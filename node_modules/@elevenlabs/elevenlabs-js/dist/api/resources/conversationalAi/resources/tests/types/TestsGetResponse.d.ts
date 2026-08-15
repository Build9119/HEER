import type * as ElevenLabs from "../../../../../index";
export type TestsGetResponse = ElevenLabs.conversationalAi.TestsGetResponse.Llm | ElevenLabs.conversationalAi.TestsGetResponse.Tool | ElevenLabs.conversationalAi.TestsGetResponse.Simulation;
export declare namespace TestsGetResponse {
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
