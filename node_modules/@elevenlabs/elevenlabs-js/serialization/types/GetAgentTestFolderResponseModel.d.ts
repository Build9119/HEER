import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AgentTestFolderPathSegmentResponseModel } from "./AgentTestFolderPathSegmentResponseModel";
export declare const GetAgentTestFolderResponseModel: core.serialization.ObjectSchema<serializers.GetAgentTestFolderResponseModel.Raw, ElevenLabs.GetAgentTestFolderResponseModel>;
export declare namespace GetAgentTestFolderResponseModel {
    interface Raw {
        id: string;
        name: string;
        folder_path?: AgentTestFolderPathSegmentResponseModel.Raw[] | null;
        children_count?: number | null;
    }
}
