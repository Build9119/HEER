import type * as ElevenLabs from "../index";
/**
 * Wrapper for anyOf/allOf composition constraints scoped to required fields.
 */
export interface RequiredConstraints {
    anyOf?: ElevenLabs.RequiredConstraint[];
    allOf?: ElevenLabs.RequiredConstraint[];
}
