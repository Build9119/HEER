import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TurnModel: core.serialization.Schema<serializers.TurnModel.Raw, ElevenLabs.TurnModel>;
export declare namespace TurnModel {
    type Raw = "turn_v2" | "turn_v3";
}
