import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ResourceAccessInfoAnonymousAccessLevelOverride: core.serialization.Schema<serializers.ResourceAccessInfoAnonymousAccessLevelOverride.Raw, ElevenLabs.ResourceAccessInfoAnonymousAccessLevelOverride>;
export declare namespace ResourceAccessInfoAnonymousAccessLevelOverride {
    type Raw = "admin" | "editor" | "commenter" | "viewer";
}
