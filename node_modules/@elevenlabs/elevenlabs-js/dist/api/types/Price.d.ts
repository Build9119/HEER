import type * as ElevenLabs from "../index";
/**
 * Currency/amount pair.
 */
export interface Price {
    amount: string;
    currency: ElevenLabs.Currency;
}
