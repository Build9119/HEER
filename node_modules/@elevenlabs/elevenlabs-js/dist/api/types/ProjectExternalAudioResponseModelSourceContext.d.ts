import type * as ElevenLabs from "../index";
export type ProjectExternalAudioResponseModelSourceContext = ElevenLabs.ProjectExternalAudioResponseModelSourceContext.MusicExploreSong | ElevenLabs.ProjectExternalAudioResponseModelSourceContext.Sfx | ElevenLabs.ProjectExternalAudioResponseModelSourceContext.Song;
export declare namespace ProjectExternalAudioResponseModelSourceContext {
    interface MusicExploreSong extends ElevenLabs.MusicExploreSongSourceContext {
        sourceType: "music_explore_song";
    }
    interface Sfx extends ElevenLabs.SfxSourceContext {
        sourceType: "sfx";
    }
    interface Song extends ElevenLabs.SongSourceContext {
        sourceType: "song";
    }
}
