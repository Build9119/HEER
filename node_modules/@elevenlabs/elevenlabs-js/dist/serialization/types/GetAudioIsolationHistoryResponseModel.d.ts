import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AudioIsolationHistoryItemResponseModel } from "./AudioIsolationHistoryItemResponseModel";
export declare const GetAudioIsolationHistoryResponseModel: core.serialization.ObjectSchema<serializers.GetAudioIsolationHistoryResponseModel.Raw, ElevenLabs.GetAudioIsolationHistoryResponseModel>;
export declare namespace GetAudioIsolationHistoryResponseModel {
    interface Raw {
        items: AudioIsolationHistoryItemResponseModel.Raw[];
        has_more: boolean;
    }
}
