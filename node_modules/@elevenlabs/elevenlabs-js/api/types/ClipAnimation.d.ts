import type * as ElevenLabs from "../index";
export interface ClipAnimation {
    enterEffect?: ElevenLabs.ClipAnimationEnterEffect;
    enterDurationMs?: number;
    exitEffect?: ElevenLabs.ClipAnimationExitEffect;
    exitDurationMs?: number;
}
