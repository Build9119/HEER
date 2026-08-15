import type * as ElevenLabs from "../../../../api/index";
import * as core from "../../../../core";
import type * as serializers from "../../../index";
import { AudioOutput } from "../../../types/AudioOutput";
import { FinalOutput } from "../../../types/FinalOutput";
export declare const ReceiveMessage: core.serialization.Schema<serializers.ReceiveMessage.Raw, ElevenLabs.ReceiveMessage>;
export declare namespace ReceiveMessage {
    type Raw = AudioOutput.Raw | FinalOutput.Raw;
}
