import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DependentAvailableToolIdentifier } from "./DependentAvailableToolIdentifier";
import { DependentUnknownToolIdentifier } from "./DependentUnknownToolIdentifier";
export declare const AuthConnectionDependenciesToolsItem: core.serialization.Schema<serializers.AuthConnectionDependenciesToolsItem.Raw, ElevenLabs.AuthConnectionDependenciesToolsItem>;
export declare namespace AuthConnectionDependenciesToolsItem {
    type Raw = AuthConnectionDependenciesToolsItem.Available | AuthConnectionDependenciesToolsItem.Unknown;
    interface Available extends DependentAvailableToolIdentifier.Raw {
        type: "available";
    }
    interface Unknown extends DependentUnknownToolIdentifier.Raw {
        type: "unknown";
    }
}
