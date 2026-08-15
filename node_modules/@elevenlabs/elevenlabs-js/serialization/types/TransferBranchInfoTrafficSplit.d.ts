import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TransferBranchInfoTrafficSplit: core.serialization.ObjectSchema<serializers.TransferBranchInfoTrafficSplit.Raw, ElevenLabs.TransferBranchInfoTrafficSplit>;
export declare namespace TransferBranchInfoTrafficSplit {
    interface Raw {
        branch_id: string;
        traffic_percentage: number;
    }
}
