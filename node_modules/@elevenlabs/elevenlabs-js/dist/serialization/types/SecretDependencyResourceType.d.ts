import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SecretDependencyResourceType: core.serialization.Schema<serializers.SecretDependencyResourceType.Raw, ElevenLabs.SecretDependencyResourceType>;
export declare namespace SecretDependencyResourceType {
    type Raw = "tools" | "agents" | "phone_numbers";
}
