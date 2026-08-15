import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SearchHighlightSegment: core.serialization.ObjectSchema<serializers.SearchHighlightSegment.Raw, ElevenLabs.SearchHighlightSegment>;
export declare namespace SearchHighlightSegment {
    interface Raw {
        value: string;
        is_hit: boolean;
    }
}
