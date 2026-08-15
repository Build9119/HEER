import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DependentBranchInfo } from "./DependentBranchInfo";
import { GetToolDependentAgentsResponseModelAgentsItem } from "./GetToolDependentAgentsResponseModelAgentsItem";
export declare const GetToolDependentAgentsResponseModel: core.serialization.ObjectSchema<serializers.GetToolDependentAgentsResponseModel.Raw, ElevenLabs.GetToolDependentAgentsResponseModel>;
export declare namespace GetToolDependentAgentsResponseModel {
    interface Raw {
        agents: GetToolDependentAgentsResponseModelAgentsItem.Raw[];
        branches?: DependentBranchInfo.Raw[] | null;
        next_cursor?: string | null;
        has_more: boolean;
    }
}
