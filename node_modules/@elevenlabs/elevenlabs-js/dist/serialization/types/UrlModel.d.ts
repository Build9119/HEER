import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UrlModel: core.serialization.ObjectSchema<serializers.UrlModel.Raw, ElevenLabs.UrlModel>;
export declare namespace UrlModel {
    interface Raw {
        url_string?: string | null;
        scheme?: string | null;
        hostname?: string | null;
        port?: number | null;
        path?: string | null;
        query_string?: string | null;
    }
}
