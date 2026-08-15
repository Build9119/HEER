import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DependentIntegrationConnectionIdentifier: core.serialization.ObjectSchema<serializers.DependentIntegrationConnectionIdentifier.Raw, ElevenLabs.DependentIntegrationConnectionIdentifier>;
export declare namespace DependentIntegrationConnectionIdentifier {
    interface Raw {
        id: string;
        name: string;
    }
}
