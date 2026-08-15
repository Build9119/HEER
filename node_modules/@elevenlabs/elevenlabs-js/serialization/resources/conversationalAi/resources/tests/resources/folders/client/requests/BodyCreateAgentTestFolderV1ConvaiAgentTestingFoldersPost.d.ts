import type * as ElevenLabs from "../../../../../../../../../api/index";
import * as core from "../../../../../../../../../core";
import type * as serializers from "../../../../../../../../index";
export declare const BodyCreateAgentTestFolderV1ConvaiAgentTestingFoldersPost: core.serialization.Schema<serializers.conversationalAi.tests.BodyCreateAgentTestFolderV1ConvaiAgentTestingFoldersPost.Raw, ElevenLabs.conversationalAi.tests.BodyCreateAgentTestFolderV1ConvaiAgentTestingFoldersPost>;
export declare namespace BodyCreateAgentTestFolderV1ConvaiAgentTestingFoldersPost {
    interface Raw {
        name: string;
        parent_folder_id?: string | null;
    }
}
