import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ConvAiFileUploadResponseModel: core.serialization.ObjectSchema<serializers.ConvAiFileUploadResponseModel.Raw, ElevenLabs.ConvAiFileUploadResponseModel>;
export declare namespace ConvAiFileUploadResponseModel {
    interface Raw {
        file_id: string;
    }
}
