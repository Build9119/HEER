import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const QuoteInfo: core.serialization.ObjectSchema<serializers.QuoteInfo.Raw, ElevenLabs.QuoteInfo>;
export declare namespace QuoteInfo {
    interface Raw {
        amount_usd: number;
    }
}
