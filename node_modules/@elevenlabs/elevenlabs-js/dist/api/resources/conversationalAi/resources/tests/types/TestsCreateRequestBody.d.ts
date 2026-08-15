import type * as ElevenLabs from "../../../../../index";
/**
 * Create Chat Response Test Request Information
 */
export type TestsCreateRequestBody = ElevenLabs.conversationalAi.TestsCreateRequestBody.Llm | ElevenLabs.conversationalAi.TestsCreateRequestBody.Tool | ElevenLabs.conversationalAi.TestsCreateRequestBody.Simulation;
export declare namespace TestsCreateRequestBody {
    interface Llm extends ElevenLabs.CreateResponseUnitTestRequest {
        type: "llm";
    }
    interface Tool extends ElevenLabs.CreateToolCallUnitTestRequest {
        type: "tool";
    }
    interface Simulation extends ElevenLabs.CreateSimulationTestRequest {
        type: "simulation";
    }
}
