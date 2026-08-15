import type * as ElevenLabs from "../index";
export type EnvironmentVariableResponseValues = Record<string, string> | Record<string, ElevenLabs.EnvironmentVariableSecretValue> | Record<string, ElevenLabs.EnvironmentVariableAuthConnectionValue>;
