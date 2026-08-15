import type * as ElevenLabs from "../../../../../../../../../api/index";
import * as core from "../../../../../../../../../core";
import type * as serializers from "../../../../../../../../index";
import { ColumnFilter } from "../../../../../../../../types/ColumnFilter";
import { BodyListApiRequestsV1WorkspaceAnalyticsRequestsPostSort } from "../../types/BodyListApiRequestsV1WorkspaceAnalyticsRequestsPostSort";
export declare const BodyListApiRequestsV1WorkspaceAnalyticsRequestsPost: core.serialization.Schema<serializers.workspace.analytics.BodyListApiRequestsV1WorkspaceAnalyticsRequestsPost.Raw, ElevenLabs.workspace.analytics.BodyListApiRequestsV1WorkspaceAnalyticsRequestsPost>;
export declare namespace BodyListApiRequestsV1WorkspaceAnalyticsRequestsPost {
    interface Raw {
        start_time?: number | null;
        end_time?: number | null;
        limit?: number | null;
        sort?: BodyListApiRequestsV1WorkspaceAnalyticsRequestsPostSort.Raw | null;
        filters?: ColumnFilter.Raw[] | null;
        search?: string | null;
    }
}
