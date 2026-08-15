import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { MusicExploreSongSourceContext } from "./MusicExploreSongSourceContext";
import { SfxSourceContext } from "./SfxSourceContext";
import { SongSourceContext } from "./SongSourceContext";
export declare const ProjectExternalAudioResponseModelSourceContext: core.serialization.Schema<serializers.ProjectExternalAudioResponseModelSourceContext.Raw, ElevenLabs.ProjectExternalAudioResponseModelSourceContext>;
export declare namespace ProjectExternalAudioResponseModelSourceContext {
    type Raw = ProjectExternalAudioResponseModelSourceContext.MusicExploreSong | ProjectExternalAudioResponseModelSourceContext.Sfx | ProjectExternalAudioResponseModelSourceContext.Song;
    interface MusicExploreSong extends MusicExploreSongSourceContext.Raw {
        source_type: "music_explore_song";
    }
    interface Sfx extends SfxSourceContext.Raw {
        source_type: "sfx";
    }
    interface Song extends SongSourceContext.Raw {
        source_type: "song";
    }
}
