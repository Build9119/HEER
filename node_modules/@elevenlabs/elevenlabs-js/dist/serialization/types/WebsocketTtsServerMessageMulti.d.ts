import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { Alignment } from "./Alignment";
import { NormalizedAlignment } from "./NormalizedAlignment";
export declare const WebsocketTtsServerMessageMulti: core.serialization.ObjectSchema<serializers.WebsocketTtsServerMessageMulti.Raw, ElevenLabs.WebsocketTtsServerMessageMulti>;
export declare namespace WebsocketTtsServerMessageMulti {
    interface Raw {
        audio?: string | null;
        is_final?: boolean | null;
        normalizedAlignment?: NormalizedAlignment.Raw | null;
        alignment?: Alignment.Raw | null;
        contextId?: string | null;
    }
}
