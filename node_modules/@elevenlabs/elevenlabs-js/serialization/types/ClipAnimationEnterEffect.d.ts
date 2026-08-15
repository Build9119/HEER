import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ClipAnimationEnterEffect: core.serialization.Schema<serializers.ClipAnimationEnterEffect.Raw, ElevenLabs.ClipAnimationEnterEffect>;
export declare namespace ClipAnimationEnterEffect {
    type Raw = "none" | "fade" | "float" | "gentle_float" | "zoom_in" | "drop" | "slide_left" | "slide_right" | "slide_up" | "slide_down" | "pop" | "bounce" | "spin" | "slide_bounce";
}
