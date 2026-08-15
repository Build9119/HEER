import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { TranscriptionWordType } from "./TranscriptionWordType";
export declare const TranscriptionWord: core.serialization.ObjectSchema<serializers.TranscriptionWord.Raw, ElevenLabs.TranscriptionWord>;
export declare namespace TranscriptionWord {
    interface Raw {
        text?: string | null;
        start?: number | null;
        end?: number | null;
        type?: TranscriptionWordType.Raw | null;
        speaker_id?: string | null;
        logprob?: number | null;
        characters?: string[] | null;
    }
}
