import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
import { GetResponseUnitTestResponseModel } from "../../../../../types/GetResponseUnitTestResponseModel";
import { GetSimulationTestResponseModel } from "../../../../../types/GetSimulationTestResponseModel";
import { GetToolCallUnitTestResponseModel } from "../../../../../types/GetToolCallUnitTestResponseModel";
export declare const TestsUpdateResponse: core.serialization.Schema<serializers.conversationalAi.TestsUpdateResponse.Raw, ElevenLabs.conversationalAi.TestsUpdateResponse>;
export declare namespace TestsUpdateResponse {
    type Raw = TestsUpdateResponse.Llm | TestsUpdateResponse.Tool | TestsUpdateResponse.Simulation;
    interface Llm extends GetResponseUnitTestResponseModel.Raw {
        type: "llm";
    }
    interface Tool extends GetToolCallUnitTestResponseModel.Raw {
        type: "tool";
    }
    interface Simulation extends GetSimulationTestResponseModel.Raw {
        type: "simulation";
    }
}
