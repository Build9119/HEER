import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ToolExecutionResponseModel } from "./ToolExecutionResponseModel";
export declare const GetToolExecutionsPageResponseModel: core.serialization.ObjectSchema<serializers.GetToolExecutionsPageResponseModel.Raw, ElevenLabs.GetToolExecutionsPageResponseModel>;
export declare namespace GetToolExecutionsPageResponseModel {
    interface Raw {
        executions: ToolExecutionResponseModel.Raw[];
        next_cursor?: string | null;
        has_more: boolean;
    }
}
