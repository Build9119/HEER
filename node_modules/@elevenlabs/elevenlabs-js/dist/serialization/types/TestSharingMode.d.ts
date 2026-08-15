import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TestSharingMode: core.serialization.Schema<serializers.TestSharingMode.Raw, ElevenLabs.TestSharingMode>;
export declare namespace TestSharingMode {
    type Raw = "all" | "shared_with_me";
}
