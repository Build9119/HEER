import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ClipAnimationEnterEffect } from "./ClipAnimationEnterEffect";
import { ClipAnimationExitEffect } from "./ClipAnimationExitEffect";
export declare const ClipAnimation: core.serialization.ObjectSchema<serializers.ClipAnimation.Raw, ElevenLabs.ClipAnimation>;
export declare namespace ClipAnimation {
    interface Raw {
        enter_effect?: ClipAnimationEnterEffect.Raw | null;
        enter_duration_ms?: number | null;
        exit_effect?: ClipAnimationExitEffect.Raw | null;
        exit_duration_ms?: number | null;
    }
}
