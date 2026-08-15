import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
import { AstBooleanNodeOutput } from "./AstBooleanNodeOutput";
import { AstDynamicVariableNodeOutput } from "./AstDynamicVariableNodeOutput";
import { AstllmNodeOutput } from "./AstllmNodeOutput";
import { AstNullNodeOutput } from "./AstNullNodeOutput";
import { AstNumberNodeOutput } from "./AstNumberNodeOutput";
import { AstStringNodeOutput } from "./AstStringNodeOutput";
export declare const AstNodeOutput: core.serialization.Schema<serializers.AstNodeOutput.Raw, ElevenLabs.AstNodeOutput>;
export declare namespace AstNodeOutput {
    type Raw = AstNodeOutput.AddOperator | AstNodeOutput.AndOperator | AstNodeOutput.BooleanLiteral | AstNodeOutput.ConditionalOperator | AstNodeOutput.DivOperator | AstNodeOutput.DynamicVariable | AstNodeOutput.EqOperator | AstNodeOutput.GtOperator | AstNodeOutput.GteOperator | AstNodeOutput.Llm | AstNodeOutput.LtOperator | AstNodeOutput.LteOperator | AstNodeOutput.MulOperator | AstNodeOutput.NeqOperator | AstNodeOutput.NullLiteral | AstNodeOutput.NumberLiteral | AstNodeOutput.OrOperator | AstNodeOutput.StringLiteral | AstNodeOutput.SubOperator;
    interface AddOperator extends serializers.AstAdditionOperatorNodeOutput.Raw {
        type: "add_operator";
    }
    interface AndOperator extends serializers.AstAndOperatorNodeOutput.Raw {
        type: "and_operator";
    }
    interface BooleanLiteral extends AstBooleanNodeOutput.Raw {
        type: "boolean_literal";
    }
    interface ConditionalOperator extends serializers.AstConditionalOperatorNodeOutput.Raw {
        type: "conditional_operator";
    }
    interface DivOperator extends serializers.AstDivisionOperatorNodeOutput.Raw {
        type: "div_operator";
    }
    interface DynamicVariable extends AstDynamicVariableNodeOutput.Raw {
        type: "dynamic_variable";
    }
    interface EqOperator extends serializers.AstEqualsOperatorNodeOutput.Raw {
        type: "eq_operator";
    }
    interface GtOperator extends serializers.AstGreaterThanOperatorNodeOutput.Raw {
        type: "gt_operator";
    }
    interface GteOperator extends serializers.AstGreaterThanOrEqualsOperatorNodeOutput.Raw {
        type: "gte_operator";
    }
    interface Llm extends AstllmNodeOutput.Raw {
        type: "llm";
    }
    interface LtOperator extends serializers.AstLessThanOperatorNodeOutput.Raw {
        type: "lt_operator";
    }
    interface LteOperator extends serializers.AstLessThanOrEqualsOperatorNodeOutput.Raw {
        type: "lte_operator";
    }
    interface MulOperator extends serializers.AstMultiplicationOperatorNodeOutput.Raw {
        type: "mul_operator";
    }
    interface NeqOperator extends serializers.AstNotEqualsOperatorNodeOutput.Raw {
        type: "neq_operator";
    }
    interface NullLiteral extends AstNullNodeOutput.Raw {
        type: "null_literal";
    }
    interface NumberLiteral extends AstNumberNodeOutput.Raw {
        type: "number_literal";
    }
    interface OrOperator extends serializers.AstOrOperatorNodeOutput.Raw {
        type: "or_operator";
    }
    interface StringLiteral extends AstStringNodeOutput.Raw {
        type: "string_literal";
    }
    interface SubOperator extends serializers.AstSubtractionOperatorNodeOutput.Raw {
        type: "sub_operator";
    }
}
