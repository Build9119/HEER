import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ProjectMutedTracksResponseModel: core.serialization.ObjectSchema<serializers.ProjectMutedTracksResponseModel.Raw, ElevenLabs.ProjectMutedTracksResponseModel>;
export declare namespace ProjectMutedTracksResponseModel {
    interface Raw {
        chapter_ids: string[];
    }
}
