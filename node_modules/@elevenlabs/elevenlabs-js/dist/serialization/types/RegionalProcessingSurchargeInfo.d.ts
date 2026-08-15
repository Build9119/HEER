import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const RegionalProcessingSurchargeInfo: core.serialization.ObjectSchema<serializers.RegionalProcessingSurchargeInfo.Raw, ElevenLabs.RegionalProcessingSurchargeInfo>;
export declare namespace RegionalProcessingSurchargeInfo {
    interface Raw {
        multiplier: number;
    }
}
