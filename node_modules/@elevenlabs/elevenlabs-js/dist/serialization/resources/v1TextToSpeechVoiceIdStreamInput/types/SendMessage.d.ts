import type * as ElevenLabs from "../../../../api/index";
import * as core from "../../../../core";
import type * as serializers from "../../../index";
import { CloseConnection } from "../../../types/CloseConnection";
import { InitializeConnection } from "../../../types/InitializeConnection";
import { SendText } from "../../../types/SendText";
export declare const SendMessage: core.serialization.Schema<serializers.SendMessage.Raw, ElevenLabs.SendMessage>;
export declare namespace SendMessage {
    type Raw = InitializeConnection.Raw | SendText.Raw | CloseConnection.Raw;
}
