import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { Currency } from "./Currency";
export declare const Price: core.serialization.ObjectSchema<serializers.Price.Raw, ElevenLabs.Price>;
export declare namespace Price {
    interface Raw {
        amount: string;
        currency: Currency.Raw;
    }
}
