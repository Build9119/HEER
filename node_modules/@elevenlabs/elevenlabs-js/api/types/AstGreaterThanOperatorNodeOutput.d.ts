import type * as ElevenLabs from "../index";
export interface AstGreaterThanOperatorNodeOutput {
    /** Left operand of the binary operator. */
    left: ElevenLabs.AstNodeOutput;
    /** Right operand of the binary operator. */
    right: ElevenLabs.AstNodeOutput;
}
