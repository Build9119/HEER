import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DependentAvailableMcpServerIdentifier } from "./DependentAvailableMcpServerIdentifier";
import { DependentUnknownMcpServerIdentifier } from "./DependentUnknownMcpServerIdentifier";
export declare const AuthConnectionDependenciesMcpServersItem: core.serialization.Schema<serializers.AuthConnectionDependenciesMcpServersItem.Raw, ElevenLabs.AuthConnectionDependenciesMcpServersItem>;
export declare namespace AuthConnectionDependenciesMcpServersItem {
    type Raw = AuthConnectionDependenciesMcpServersItem.Available | AuthConnectionDependenciesMcpServersItem.Unknown;
    interface Available extends DependentAvailableMcpServerIdentifier.Raw {
        type: "available";
    }
    interface Unknown extends DependentUnknownMcpServerIdentifier.Raw {
        type: "unknown";
    }
}
