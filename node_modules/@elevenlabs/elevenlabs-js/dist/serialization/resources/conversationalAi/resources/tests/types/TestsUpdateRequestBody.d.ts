import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
import { UpdateResponseUnitTestRequest } from "../../../../../types/UpdateResponseUnitTestRequest";
import { UpdateSimulationTestRequest } from "../../../../../types/UpdateSimulationTestRequest";
import { UpdateToolCallUnitTestRequest } from "../../../../../types/UpdateToolCallUnitTestRequest";
export declare const TestsUpdateRequestBody: core.serialization.Schema<serializers.conversationalAi.TestsUpdateRequestBody.Raw, ElevenLabs.conversationalAi.TestsUpdateRequestBody>;
export declare namespace TestsUpdateRequestBody {
    type Raw = TestsUpdateRequestBody.Llm | TestsUpdateRequestBody.Tool | TestsUpdateRequestBody.Simulation;
    interface Llm extends UpdateResponseUnitTestRequest.Raw {
        type: "llm";
    }
    interface Tool extends UpdateToolCallUnitTestRequest.Raw {
        type: "tool";
    }
    interface Simulation extends UpdateSimulationTestRequest.Raw {
        type: "simulation";
    }
}
