import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { GetSecretDependenciesResponseModelDependencies } from "./GetSecretDependenciesResponseModelDependencies";
export declare const GetSecretDependenciesResponseModel: core.serialization.ObjectSchema<serializers.GetSecretDependenciesResponseModel.Raw, ElevenLabs.GetSecretDependenciesResponseModel>;
export declare namespace GetSecretDependenciesResponseModel {
    interface Raw {
        dependencies: GetSecretDependenciesResponseModelDependencies.Raw;
        next_cursor?: string | null;
    }
}
