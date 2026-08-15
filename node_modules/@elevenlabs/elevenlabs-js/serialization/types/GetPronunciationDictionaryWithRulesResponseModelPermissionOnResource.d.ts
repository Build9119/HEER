import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GetPronunciationDictionaryWithRulesResponseModelPermissionOnResource: core.serialization.Schema<serializers.GetPronunciationDictionaryWithRulesResponseModelPermissionOnResource.Raw, ElevenLabs.GetPronunciationDictionaryWithRulesResponseModelPermissionOnResource>;
export declare namespace GetPronunciationDictionaryWithRulesResponseModelPermissionOnResource {
    type Raw = "admin" | "editor" | "commenter" | "viewer";
}
