import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeviceModel: core.serialization.ObjectSchema<serializers.DeviceModel.Raw, ElevenLabs.DeviceModel>;
export declare namespace DeviceModel {
    interface Raw {
        ip?: string | null;
        hostname?: string | null;
        type_id?: number | null;
    }
}
