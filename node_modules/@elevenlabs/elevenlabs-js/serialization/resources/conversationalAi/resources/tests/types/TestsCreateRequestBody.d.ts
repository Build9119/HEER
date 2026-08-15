import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
import { CreateResponseUnitTestRequest } from "../../../../../types/CreateResponseUnitTestRequest";
import { CreateSimulationTestRequest } from "../../../../../types/CreateSimulationTestRequest";
import { CreateToolCallUnitTestRequest } from "../../../../../types/CreateToolCallUnitTestRequest";
export declare const TestsCreateRequestBody: core.serialization.Schema<serializers.conversationalAi.TestsCreateRequestBody.Raw, ElevenLabs.conversationalAi.TestsCreateRequestBody>;
export declare namespace TestsCreateRequestBody {
    type Raw = TestsCreateRequestBody.Llm | TestsCreateRequestBody.Tool | TestsCreateRequestBody.Simulation;
    interface Llm extends CreateResponseUnitTestRequest.Raw {
        type: "llm";
    }
    interface Tool extends CreateToolCallUnitTestRequest.Raw {
        type: "tool";
    }
    interface Simulation extends CreateSimulationTestRequest.Raw {
        type: "simulation";
    }
}
