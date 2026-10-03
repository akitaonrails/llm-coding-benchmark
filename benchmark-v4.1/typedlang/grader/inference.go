package grader

import (
	"testing"

	"v41lang/harness"
)

// ---------------------------------------------------------------------------
// Type inference (accept/reject). TypeCheck is the graded entry point.
// ---------------------------------------------------------------------------

// RunLetPolymorphism: a let-bound identity used at two distinct types must
// type-check (requires let-generalization). A monomorphic-let implementation
// rejects these.
func RunLetPolymorphism(t *testing.T, mk harness.MakeLangFunc) {
	expectWellTyped(t, mk, "id_at_int_and_bool",
		`let id = \x -> x in let a = id 1 in let b = id true in a`)
	expectWellTyped(t, mk, "id_applied_to_id",
		`let id = \x -> x in id id`)
	expectWellTyped(t, mk, "polymorphic_pair_fn",
		`let k = \x -> \y -> x in let a = k 1 true in let b = k false 2 in a`)
	expectWellTyped(t, mk, "let_rec_generalizes",
		`let rec len = \xs -> if null xs then 0 else 1 + len (tail xs) in (len [1,2]) + (len [true])`)
	// control: without a let, a lambda parameter is monomorphic and this is a
	// genuine type error — accepting it would be unsound, so it must be rejected
	// by EVERY correct-or-monomorphic implementation alike (shared negative).
	expectIllTyped(t, mk, "lambda_param_not_generalized",
		`(\id -> let a = id 1 in id true) (\x -> x)`)
}

// RunOccursCheck: self-application builds an infinite type and must be rejected.
func RunOccursCheck(t *testing.T, mk harness.MakeLangFunc) {
	expectIllTyped(t, mk, "self_application", `\x -> x x`)
	expectIllTyped(t, mk, "omega", `(\x -> x x) (\x -> x x)`)
	expectIllTyped(t, mk, "infinite_via_cons", `\x -> cons x x`)
	// control: structurally similar but finite -> must be accepted.
	expectWellTyped(t, mk, "finite_apply", `\f -> \x -> f x`)
}

// RunValueRestriction: generalizing a non-value (a ref cell) is unsound; using
// the one cell at two element types must be rejected.
func RunValueRestriction(t *testing.T, mk harness.MakeLangFunc) {
	expectIllTyped(t, mk, "ref_used_at_two_types",
		`let r = ref (\x -> x) in let _ = (!r) 1 in (!r) true`)
	expectIllTyped(t, mk, "nonvalue_app_not_generalized",
		`let f = (\x -> x) (\y -> y) in let _ = f 1 in f true`)
	// control: a genuine syntactic value (a lambda) SHOULD generalize.
	expectWellTyped(t, mk, "lambda_value_generalizes",
		`let id = \x -> x in let _ = id 1 in id true`)
}

// RunRowPolymorphism: a function over "records with at least field a" accepts
// records with different extra fields and rejects a record lacking a. A non-row
// (textbook W) implementation cannot accept both {a,b} and {a,c} at one call.
func RunRowPolymorphism(t *testing.T, mk harness.MakeLangFunc) {
	expectWellTyped(t, mk, "accepts_a_b_and_a_c",
		`let f = \r -> r.a in (f {a = 1, b = 2}) + (f {a = 3, c = 4})`)
	expectWellTyped(t, mk, "accepts_extra_fields",
		`let getx = \r -> r.x in getx {x = 1, y = 2, z = 3}`)
	expectWellTyped(t, mk, "two_field_constraint",
		`let f = \r -> r.a + r.b in f {a = 1, b = 2, c = 3}`)
	expectWellTyped(t, mk, "update_is_row_poly",
		`let bump = \r -> {r | a = r.a + 1} in (bump {a = 1, b = 2}).a + (bump {a = 5, z = 9}).a`)
	// rejects: the record lacks the demanded field.
	expectIllTyped(t, mk, "rejects_missing_field",
		`let f = \r -> r.a in f {b = 2}`)
	expectIllTyped(t, mk, "rejects_missing_field_direct", `{b = 2}.a`)
}

// RunTypeErrors: a battery of ill-typed programs (each rejected) plus well-typed
// near-misses (each accepted).
func RunTypeErrors(t *testing.T, mk harness.MakeLangFunc) {
	ill := []struct{ name, src string }{
		{"int_plus_bool", `1 + true`},
		{"bool_plus_int", `true + 1`},
		{"if_nonbool_cond", `if 1 then 2 else 3`},
		{"if_branch_mismatch", `if true then 1 else false`},
		{"apply_non_function", `1 2`},
		{"apply_int_arg_to_not", `not 5`},
		{"string_plus_int", `"a" + 1`},
		{"concat_ints", `1 ^ 2`},
		{"compare_bools", `true < false`},
		{"head_of_int", `head 5`},
		{"heterogeneous_list", `[1, true]`},
		{"heterogeneous_list2", `[1, "a", 2]`},
		{"unbound_var", `x + 1`},
		{"field_of_int", `(5).a`},
		{"deref_non_ref", `!5`},
		{"assign_non_ref", `5 := 6`},
		{"ref_store_wrong_type", `let r = ref 1 in r := true`},
		{"cons_type_mismatch", `cons 1 [true]`},
		{"dup_field_literal", `{a = 1, a = 2}`},
		{"record_field_type_mismatch", `let r = {a = 1} in r.a ^ "x"`},
		{"update_missing_field_closed", `let f = \r -> {r | a = 1} in f {b = 2}`},
	}
	for _, c := range ill {
		expectIllTyped(t, mk, "ill/"+c.name, c.src)
	}

	ok := []struct{ name, src string }{
		{"well_typed_arith", `1 + 2 * 3`},
		{"well_typed_if", `if true then 1 else 2`},
		{"well_typed_list", `[1, 2, 3]`},
		{"well_typed_string_concat", `"a" ^ "b"`},
		{"well_typed_ref", `let r = ref 1 in r := 2`},
		{"well_typed_record", `let r = {a = 1, b = "x"} in r.b`},
		{"well_typed_poly_list_builtins", `let rec len = \xs -> if null xs then 0 else 1 + len (tail xs) in len`},
		{"well_typed_higher_order", `(\f -> \x -> f (f x)) (\n -> n + 1) 0`},
		{"well_typed_nested_record", `{outer = {inner = 1}}`},
		{"well_typed_update", `let r = {a = 1, b = 2} in {r | a = 99}`},
	}
	for _, c := range ok {
		expectWellTyped(t, mk, "ok/"+c.name, c.src)
	}
}
