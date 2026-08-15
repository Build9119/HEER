import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const EnvironmentAuthConnectionLocator: core.serialization.ObjectSchema<serializers.EnvironmentAuthConnectionLocator.Raw, ElevenLabs.EnvironmentAuthConnectionLocator>;
export declare namespace EnvironmentAuthConnectionLocator {
    interface Raw {
        env_var_label: string;
    }
}
