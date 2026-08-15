import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
export declare const TestsListRequestSortMode: core.serialization.Schema<serializers.conversationalAi.TestsListRequestSortMode.Raw, ElevenLabs.conversationalAi.TestsListRequestSortMode>;
export declare namespace TestsListRequestSortMode {
    type Raw = "default" | "folders_first";
}
