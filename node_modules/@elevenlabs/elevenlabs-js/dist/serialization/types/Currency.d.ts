import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const Currency: core.serialization.Schema<serializers.Currency.Raw, ElevenLabs.Currency>;
export declare namespace Currency {
    type Raw = "usd" | "eur" | "inr" | "pln";
}
