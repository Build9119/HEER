import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { GetPronunciationDictionaryWithRulesResponseModelPermissionOnResource } from "./GetPronunciationDictionaryWithRulesResponseModelPermissionOnResource";
import { GetPronunciationDictionaryWithRulesResponseModelRulesItem } from "./GetPronunciationDictionaryWithRulesResponseModelRulesItem";
export declare const GetPronunciationDictionaryWithRulesResponseModel: core.serialization.ObjectSchema<serializers.GetPronunciationDictionaryWithRulesResponseModel.Raw, ElevenLabs.GetPronunciationDictionaryWithRulesResponseModel>;
export declare namespace GetPronunciationDictionaryWithRulesResponseModel {
    interface Raw {
        id: string;
        latest_version_id: string;
        latest_version_rules_num: number;
        name: string;
        permission_on_resource?: GetPronunciationDictionaryWithRulesResponseModelPermissionOnResource.Raw | null;
        created_by: string;
        creation_time_unix: number;
        archived_time_unix?: number | null;
        description?: string | null;
        rules: GetPronunciationDictionaryWithRulesResponseModelRulesItem.Raw[];
    }
}
