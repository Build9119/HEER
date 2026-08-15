import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const StudioTextStyleShadowModel: core.serialization.ObjectSchema<serializers.StudioTextStyleShadowModel.Raw, ElevenLabs.StudioTextStyleShadowModel>;
export declare namespace StudioTextStyleShadowModel {
    interface Raw {
        enabled: boolean;
        color: string;
        opacity: number;
        blur: number;
        offset_x: number;
        offset_y: number;
    }
}
