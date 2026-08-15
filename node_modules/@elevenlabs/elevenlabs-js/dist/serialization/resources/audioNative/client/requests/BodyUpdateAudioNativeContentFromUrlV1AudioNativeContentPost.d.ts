import type * as ElevenLabs from "../../../../../api/index";
import * as core from "../../../../../core";
import type * as serializers from "../../../../index";
export declare const BodyUpdateAudioNativeContentFromUrlV1AudioNativeContentPost: core.serialization.Schema<serializers.BodyUpdateAudioNativeContentFromUrlV1AudioNativeContentPost.Raw, ElevenLabs.BodyUpdateAudioNativeContentFromUrlV1AudioNativeContentPost>;
export declare namespace BodyUpdateAudioNativeContentFromUrlV1AudioNativeContentPost {
    interface Raw {
        url: string;
        author?: string | null;
        title?: string | null;
    }
}
