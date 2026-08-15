import type * as ElevenLabs from "../../../../api/index";
import * as core from "../../../../core";
import type * as serializers from "../../../index";
import { AudioOutputMulti } from "../../../types/AudioOutputMulti";
import { FinalOutputMulti } from "../../../types/FinalOutputMulti";
export declare const ReceiveMessageMulti: core.serialization.Schema<serializers.ReceiveMessageMulti.Raw, ElevenLabs.ReceiveMessageMulti>;
export declare namespace ReceiveMessageMulti {
    type Raw = AudioOutputMulti.Raw | FinalOutputMulti.Raw;
}
