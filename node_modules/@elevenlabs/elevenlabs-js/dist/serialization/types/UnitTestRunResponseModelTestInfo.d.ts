import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ResponseUnitTestModel } from "./ResponseUnitTestModel";
import { SimulationTestModel } from "./SimulationTestModel";
import { ToolCallUnitTestModel } from "./ToolCallUnitTestModel";
export declare const UnitTestRunResponseModelTestInfo: core.serialization.Schema<serializers.UnitTestRunResponseModelTestInfo.Raw, ElevenLabs.UnitTestRunResponseModelTestInfo>;
export declare namespace UnitTestRunResponseModelTestInfo {
    type Raw = UnitTestRunResponseModelTestInfo.Llm | UnitTestRunResponseModelTestInfo.Simulation | UnitTestRunResponseModelTestInfo.Tool;
    interface Llm extends ResponseUnitTestModel.Raw {
        type: "llm";
    }
    interface Simulation extends SimulationTestModel.Raw {
        type: "simulation";
    }
    interface Tool extends ToolCallUnitTestModel.Raw {
        type: "tool";
    }
}
