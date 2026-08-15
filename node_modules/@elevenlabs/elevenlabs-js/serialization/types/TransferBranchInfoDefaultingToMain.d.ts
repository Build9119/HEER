import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TransferBranchInfoDefaultingToMain: core.serialization.ObjectSchema<serializers.TransferBranchInfoDefaultingToMain.Raw, ElevenLabs.TransferBranchInfoDefaultingToMain>;
export declare namespace TransferBranchInfoDefaultingToMain {
    interface Raw {
        branch_id: string;
    }
}
