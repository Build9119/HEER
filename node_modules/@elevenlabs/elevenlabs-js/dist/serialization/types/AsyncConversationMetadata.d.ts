import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AsyncConversationMetadataDeliveryStatus } from "./AsyncConversationMetadataDeliveryStatus";
export declare const AsyncConversationMetadata: core.serialization.ObjectSchema<serializers.AsyncConversationMetadata.Raw, ElevenLabs.AsyncConversationMetadata>;
export declare namespace AsyncConversationMetadata {
    interface Raw {
        delivery_status: AsyncConversationMetadataDeliveryStatus.Raw;
        delivery_timestamp: number;
        delivery_error?: string | null;
        external_system: string;
        external_id: string;
        external_link?: string | null;
        retry_count?: number | null;
        last_retry_timestamp?: number | null;
        last_processed_external_message_id?: string | null;
    }
}
