import type * as ElevenLabs from "../../../../../index";
/**
 * Agent test to update
 */
export type TestsUpdateRequestBody = ElevenLabs.conversationalAi.TestsUpdateRequestBody.Llm | ElevenLabs.conversationalAi.TestsUpdateRequestBody.Tool | ElevenLabs.conversationalAi.TestsUpdateRequestBody.Simulation;
export declare namespace TestsUpdateRequestBody {
    interface Llm extends ElevenLabs.UpdateResponseUnitTestRequest {
        type: "llm";
    }
    interface Tool extends ElevenLabs.UpdateToolCallUnitTestRequest {
        type: "tool";
    }
    interface Simulation extends ElevenLabs.UpdateSimulationTestRequest {
        type: "simulation";
    }
}
