import type * as ElevenLabs from "../../../../../../../api/index";
import * as core from "../../../../../../../core";
import type * as serializers from "../../../../../../index";
export declare const BodyBulkMoveTestsToFolderV1ConvaiAgentTestingBulkMovePost: core.serialization.Schema<serializers.conversationalAi.BodyBulkMoveTestsToFolderV1ConvaiAgentTestingBulkMovePost.Raw, ElevenLabs.conversationalAi.BodyBulkMoveTestsToFolderV1ConvaiAgentTestingBulkMovePost>;
export declare namespace BodyBulkMoveTestsToFolderV1ConvaiAgentTestingBulkMovePost {
    interface Raw {
        entity_ids: string[];
        move_to?: string | null;
    }
}
