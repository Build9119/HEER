import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateAgentTestFolderResponseModel: core.serialization.ObjectSchema<serializers.CreateAgentTestFolderResponseModel.Raw, ElevenLabs.CreateAgentTestFolderResponseModel>;
export declare namespace CreateAgentTestFolderResponseModel {
    interface Raw {
        id: string;
        name: string;
    }
}
