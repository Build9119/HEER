import type * as ElevenLabs from "../../../../../../../../api/index";
import * as core from "../../../../../../../../core";
import type * as serializers from "../../../../../../../index";
import { GetKnowledgeBaseFileResponseModel } from "../../../../../../../types/GetKnowledgeBaseFileResponseModel";
import { GetKnowledgeBaseFolderResponseModel } from "../../../../../../../types/GetKnowledgeBaseFolderResponseModel";
import { GetKnowledgeBaseTextResponseModel } from "../../../../../../../types/GetKnowledgeBaseTextResponseModel";
import { GetKnowledgeBaseUrlResponseModel } from "../../../../../../../types/GetKnowledgeBaseUrlResponseModel";
export declare const DocumentUpdateFileResponse: core.serialization.Schema<serializers.conversationalAi.knowledgeBase.DocumentUpdateFileResponse.Raw, ElevenLabs.conversationalAi.knowledgeBase.DocumentUpdateFileResponse>;
export declare namespace DocumentUpdateFileResponse {
    type Raw = DocumentUpdateFileResponse.Url | DocumentUpdateFileResponse.File | DocumentUpdateFileResponse.Text | DocumentUpdateFileResponse.Folder;
    interface Url extends GetKnowledgeBaseUrlResponseModel.Raw {
        type: "url";
    }
    interface File extends GetKnowledgeBaseFileResponseModel.Raw {
        type: "file";
    }
    interface Text extends GetKnowledgeBaseTextResponseModel.Raw {
        type: "text";
    }
    interface Folder extends GetKnowledgeBaseFolderResponseModel.Raw {
        type: "folder";
    }
}
