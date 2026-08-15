import type * as ElevenLabs from "../index";
/**
 * The API key for authentication. Either a workspace secret reference {'secret_id': '...'} or an environment variable reference {'env_var_label': '...'}.
 */
export type CustomLlmApiKey = ElevenLabs.ConvAiSecretLocator | ElevenLabs.ConvAiEnvVarLocator;
