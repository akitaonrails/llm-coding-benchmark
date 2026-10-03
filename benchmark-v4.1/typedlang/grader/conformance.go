package grader

import (
	"testing"

	"v41lang/harness"
)

// ---------------------------------------------------------------------------
// Conformance: program -> EXACT stdout (SPEC §5).
// ---------------------------------------------------------------------------

func RunBasicEval(t *testing.T, mk harness.MakeLangFunc) {
	runConformance(t, mk, []conformCase{
		{"int_arith", `print (1 + 2 * 3 - 4)`, "3\n"},
		{"div_trunc", `print (10 / 3)`, "3\n"},
		{"neg", `print (0 - 7)`, "-7\n"},
		{"unary_neg", `print (-9)`, "-9\n"},
		{"bool", `print (1 < 2)`, "true\n"},
		{"not", `print (not (1 == 1))`, "false\n"},
		{"if", `print (if 2 <= 2 then 10 else 20)`, "10\n"},
		{"string", `print "hello"`, "\"hello\"\n"},
		{"string_escape", `print "a\tb\nc\"d\\e"`, "\"a\\tb\\nc\\\"d\\\\e\"\n"},
		{"concat", `print ("foo" ^ "bar")`, "\"foobar\"\n"},
		{"let_seq", `let x = 2 in let y = 3 in print (x * y)`, "6\n"},
		{"print_returns", `print (print 1 + print 2)`, "1\n2\n3\n"},
	})
}

func RunClosures(t *testing.T, mk harness.MakeLangFunc) {
	runConformance(t, mk, []conformCase{
		{"identity", `let id = \x -> x in print (id 42)`, "42\n"},
		{"apply", `let apply = \f -> \x -> f x in print (apply (\n -> n + 1) 10)`, "11\n"},
		{"capture", `let a = 100 in let f = \x -> x + a in print (f 1)`, "101\n"},
		{"curry", `let add = \x -> \y -> x + y in let inc = add 1 in print (inc 41)`, "42\n"},
		{"higher_order", `let twice = \f -> \x -> f (f x) in print (twice (\n -> n * 2) 5)`, "20\n"},
		{"shadowing", `let x = 1 in let x = x + 10 in print x`, "11\n"},
		{"multi_param", `let f = \a b c -> a + b + c in print (f 1 2 3)`, "6\n"},
	})
}

func RunRecursion(t *testing.T, mk harness.MakeLangFunc) {
	runConformance(t, mk, []conformCase{
		{"factorial", `let rec fact = \n -> if n == 0 then 1 else n * fact (n - 1) in print (fact 6)`, "720\n"},
		{"fib", `let rec fib = \n -> if n < 2 then n else fib (n - 1) + fib (n - 2) in print (fib 15)`, "610\n"},
		{"tail_sum", `let rec sum = \acc -> \n -> if n == 0 then acc else sum (acc + n) (n - 1) in print (sum 0 10000)`, "50005000\n"},
		{"deep_tail", `let rec loop = \n -> if n == 0 then 777 else loop (n - 1) in print (loop 2000000)`, "777\n"},
		{"ackermann_small", `let rec ack = \m -> \n -> if m == 0 then n + 1 else if n == 0 then ack (m - 1) 1 else ack (m - 1) (ack m (n - 1)) in print (ack 2 3)`, "9\n"},
	})
}

func RunRecords(t *testing.T, mk harness.MakeLangFunc) {
	runConformance(t, mk, []conformCase{
		{"literal_sorted", `print {b = true, a = 1}`, "{a = 1, b = true}\n"},
		{"empty", `print {}`, "{}\n"},
		{"access", `let r = {x = 3, y = 4} in print (r.x + r.y)`, "7\n"},
		{"nested", `print {p = {a = 1}, q = [2, 3]}`, "{p = {a = 1}, q = [2, 3]}\n"},
		{"string_field", `print {name = "ann", age = 30}`, "{age = 30, name = \"ann\"}\n"},
		{"field_of_call", `let mk = \v -> {val = v} in print (mk 5).val`, "5\n"},
		{"poly_access", `let get = \r -> r.a in print ((get {a = 1, b = 2}) + (get {a = 10, c = 3}))`, "11\n"},
	})
}

func RunRecordUpdate(t *testing.T, mk harness.MakeLangFunc) {
	runConformance(t, mk, []conformCase{
		{"update_one", `let r = {a = 1, b = 2} in print {r | a = 9}`, "{a = 9, b = 2}\n"},
		{"update_keeps_rest", `let r = {a = 1, b = 2, c = 3} in print ({r | b = 20}).b`, "20\n"},
		{"update_two", `let r = {x = 1, y = 2, z = 3} in print {r | x = 10, z = 30}`, "{x = 10, y = 2, z = 30}\n"},
		{"update_type_change", `let r = {a = 1, b = 2} in print {r | a = true}`, "{a = true, b = 2}\n"},
		{"update_immutable", `let r = {a = 1} in let s = {r | a = 2} in print (r.a + s.a)`, "3\n"},
	})
}

func RunLists(t *testing.T, mk harness.MakeLangFunc) {
	runConformance(t, mk, []conformCase{
		{"literal", `print [1, 2, 3]`, "[1, 2, 3]\n"},
		{"empty", `print []`, "[]\n"},
		{"cons", `print (cons 1 (cons 2 (cons 3 [])))`, "[1, 2, 3]\n"},
		{"head_tail", `print (head [5, 6, 7])`, "5\n"},
		{"tail", `print (tail [5, 6, 7])`, "[6, 7]\n"},
		{"null", `let _ = print (null []) in print (null [1])`, "true\nfalse\n"},
		{"nested", `print [[1, 2], [], [3]]`, "[[1, 2], [], [3]]\n"},
		{"strings", `print ["a", "b", "c"]`, "[\"a\", \"b\", \"c\"]\n"},
		{"length_rec", `let rec len = \xs -> if null xs then 0 else 1 + len (tail xs) in print (len [10, 20, 30, 40])`, "4\n"},
		{"map_rec", `let rec map = \f -> \xs -> if null xs then [] else cons (f (head xs)) (map f (tail xs)) in print (map (\n -> n * n) [1, 2, 3, 4])`, "[1, 4, 9, 16]\n"},
	})
}
