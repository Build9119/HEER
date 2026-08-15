import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DependentPhoneNumberIdentifier } from "./DependentPhoneNumberIdentifier";
import { GetSecretDependenciesResponseModelDependenciesOneItem } from "./GetSecretDependenciesResponseModelDependenciesOneItem";
import { GetSecretDependenciesResponseModelDependenciesZeroItem } from "./GetSecretDependenciesResponseModelDependenciesZeroItem";
export declare const GetSecretDependenciesResponseModelDependencies: core.serialization.Schema<serializers.GetSecretDependenciesResponseModelDependencies.Raw, ElevenLabs.GetSecretDependenciesResponseModelDependencies>;
export declare namespace GetSecretDependenciesResponseModelDependencies {
    type Raw = GetSecretDependenciesResponseModelDependenciesZeroItem.Raw[] | GetSecretDependenciesResponseModelDependenciesOneItem.Raw[] | DependentPhoneNumberIdentifier.Raw[];
}
