import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DependentBranchInfo: core.serialization.ObjectSchema<serializers.DependentBranchInfo.Raw, ElevenLabs.DependentBranchInfo>;
export declare namespace DependentBranchInfo {
    interface Raw {
        agent_id: string;
        agent_name: string;
        branch_id: string;
        branch_name: string;
        is_main: boolean;
    }
}
