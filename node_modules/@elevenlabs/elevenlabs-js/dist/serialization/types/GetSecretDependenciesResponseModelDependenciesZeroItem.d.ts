import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DependentAvailableToolIdentifier } from "./DependentAvailableToolIdentifier";
import { DependentUnknownToolIdentifier } from "./DependentUnknownToolIdentifier";
export declare const GetSecretDependenciesResponseModelDependenciesZeroItem: core.serialization.Schema<serializers.GetSecretDependenciesResponseModelDependenciesZeroItem.Raw, ElevenLabs.GetSecretDependenciesResponseModelDependenciesZeroItem>;
export declare namespace GetSecretDependenciesResponseModelDependenciesZeroItem {
    type Raw = GetSecretDependenciesResponseModelDependenciesZeroItem.Available | GetSecretDependenciesResponseModelDependenciesZeroItem.Unknown;
    interface Available extends DependentAvailableToolIdentifier.Raw {
        type: "available";
    }
    interface Unknown extends DependentUnknownToolIdentifier.Raw {
        type: "unknown";
    }
}
