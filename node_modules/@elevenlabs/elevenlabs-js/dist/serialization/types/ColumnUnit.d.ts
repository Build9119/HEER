import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ColumnUnit: core.serialization.Schema<serializers.ColumnUnit.Raw, ElevenLabs.ColumnUnit>;
export declare namespace ColumnUnit {
    type Raw = "ms" | "s" | "min" | "duration" | "credits" | "usd" | "eur" | "inr" | "pln" | "ratio" | "rating";
}
