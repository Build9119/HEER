import type * as ElevenLabs from "../index";
/**
 * The type of tool
 */
export type PromptAgentApiModelOutputToolsItem = ElevenLabs.PromptAgentApiModelOutputToolsItem.ApiIntegrationWebhook | ElevenLabs.PromptAgentApiModelOutputToolsItem.Client | ElevenLabs.PromptAgentApiModelOutputToolsItem.Mcp | ElevenLabs.PromptAgentApiModelOutputToolsItem.Smb | ElevenLabs.PromptAgentApiModelOutputToolsItem.System | ElevenLabs.PromptAgentApiModelOutputToolsItem.Webhook;
export declare namespace PromptAgentApiModelOutputToolsItem {
    interface ApiIntegrationWebhook extends ElevenLabs.ApiIntegrationWebhookToolConfigOutput {
        type: "api_integration_webhook";
    }
    interface Client extends ElevenLabs.ClientToolConfigOutput {
        type: "client";
    }
    interface Mcp {
        type: "mcp";
        value?: unknown;
    }
    interface Smb {
        type: "smb";
        value?: unknown;
    }
    interface System extends ElevenLabs.SystemToolConfigOutput {
        type: "system";
    }
    interface Webhook extends ElevenLabs.WebhookToolConfigOutput {
        type: "webhook";
    }
}
