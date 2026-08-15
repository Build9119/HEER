import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const MusicExploreSongSourceContext: core.serialization.ObjectSchema<serializers.MusicExploreSongSourceContext.Raw, ElevenLabs.MusicExploreSongSourceContext>;
export declare namespace MusicExploreSongSourceContext {
    interface Raw {
        music_explore_song_id: string;
        title?: string | null;
        description?: string | null;
        bpm?: number | null;
        vocals?: string | null;
        lyrics?: string | null;
    }
}
