import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const StudioTextStyleOutlineModel: core.serialization.ObjectSchema<serializers.StudioTextStyleOutlineModel.Raw, ElevenLabs.StudioTextStyleOutlineModel>;
export declare namespace StudioTextStyleOutlineModel {
    interface Raw {
        enabled: boolean;
        color: string;
        opacity: number;
        width: number;
    }
}
