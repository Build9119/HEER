import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { UrlModel } from "./UrlModel";
export declare const HttpRequestModel: core.serialization.ObjectSchema<serializers.HttpRequestModel.Raw, ElevenLabs.HttpRequestModel>;
export declare namespace HttpRequestModel {
    interface Raw {
        http_method: string;
        url: UrlModel.Raw;
        user_agent?: string | null;
        x_forwarded_for?: string[] | null;
    }
}
