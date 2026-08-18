// LlmLang pure subset VM — Go runtime (not Python).
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strconv"
	"time"
)

type Instr struct {
	Op  string
	Arg interface{}
}

func (i *Instr) UnmarshalJSON(b []byte) error {
	var raw []interface{}
	if err := json.Unmarshal(b, &raw); err != nil {
		return err
	}
	i.Op, _ = raw[0].(string)
	if len(raw) > 1 {
		i.Arg = raw[1]
	}
	return nil
}

type CodeObject struct {
	Version int           `json:"version"`
	Names   []string      `json:"names"`
	Consts  []interface{} `json:"consts"`
	Code    []Instr       `json:"code"`
}

type Result struct {
	OK     bool        `json:"ok"`
	Output []string    `json:"output"`
	Error  string      `json:"error,omitempty"`
	Value  interface{} `json:"value,omitempty"`
	Steps  int         `json:"steps"`
	Ms     float64     `json:"ms"`
}

func asFloat(v interface{}) (float64, bool) {
	switch x := v.(type) {
	case float64:
		return x, true
	case int:
		return float64(x), true
	case string:
		f, err := strconv.ParseFloat(x, 64)
		return f, err == nil
	default:
		return 0, false
	}
}

func truthy(v interface{}) bool {
	if v == nil {
		return false
	}
	switch x := v.(type) {
	case bool:
		return x
	case float64:
		return x != 0
	case string:
		return x != ""
	default:
		return true
	}
}

func binOp(op string, a, b interface{}) (interface{}, error) {
	af, aok := asFloat(a)
	bf, bok := asFloat(b)
	switch op {
	case "BINARY_ADD":
		if aok && bok {
			return af + bf, nil
		}
		return fmt.Sprint(a) + fmt.Sprint(b), nil
	case "BINARY_SUB":
		if aok && bok {
			return af - bf, nil
		}
	case "BINARY_MUL":
		if aok && bok {
			return af * bf, nil
		}
	case "BINARY_DIV":
		if aok && bok {
			return af / bf, nil
		}
	case "BINARY_MOD":
		if aok && bok {
			return float64(int64(af) % int64(bf)), nil
		}
	case "BINARY_EQ":
		return (aok && bok && af == bf) || fmt.Sprint(a) == fmt.Sprint(b), nil
	case "BINARY_NE":
		eq, _ := binOp("BINARY_EQ", a, b)
		return !eq.(bool), nil
	case "BINARY_LT":
		if aok && bok {
			return af < bf, nil
		}
	case "BINARY_LE":
		if aok && bok {
			return af <= bf, nil
		}
	case "BINARY_GT":
		if aok && bok {
			return af > bf, nil
		}
	case "BINARY_GE":
		if aok && bok {
			return af >= bf, nil
		}
	case "BINARY_AND":
		return truthy(a) && truthy(b), nil
	case "BINARY_OR":
		return truthy(a) || truthy(b), nil
	}
	return nil, fmt.Errorf("bad binop %s", op)
}

func argInt(arg interface{}) int {
	f, _ := asFloat(arg)
	return int(f)
}

func run(code CodeObject, maxSteps int) Result {
	stack := make([]interface{}, 0, 64)
	locals := map[string]interface{}{}
	output := []string{}
	ip, steps := 0, 0
	t0 := time.Now()
	push := func(v interface{}) { stack = append(stack, v) }
	pop := func() interface{} {
		n := len(stack)
		if n == 0 {
			return nil
		}
		v := stack[n-1]
		stack = stack[:n-1]
		return v
	}
	for ip < len(code.Code) {
		steps++
		if steps > maxSteps {
			return Result{OK: false, Output: output, Error: "max steps", Steps: steps, Ms: time.Since(t0).Seconds() * 1000}
		}
		ins := code.Code[ip]
		ip++
		switch ins.Op {
		case "LOAD_CONST":
			push(code.Consts[argInt(ins.Arg)])
		case "LOAD_NAME":
			n := code.Names[argInt(ins.Arg)]
			v, ok := locals[n]
			if !ok {
				return Result{OK: false, Output: output, Error: "undefined " + n, Steps: steps, Ms: time.Since(t0).Seconds() * 1000}
			}
			push(v)
		case "STORE_NAME":
			locals[code.Names[argInt(ins.Arg)]] = pop()
		case "BINARY_ADD", "BINARY_SUB", "BINARY_MUL", "BINARY_DIV", "BINARY_MOD",
			"BINARY_EQ", "BINARY_NE", "BINARY_LT", "BINARY_LE", "BINARY_GT", "BINARY_GE",
			"BINARY_AND", "BINARY_OR":
			b, a := pop(), pop()
			r, err := binOp(ins.Op, a, b)
			if err != nil {
				return Result{OK: false, Output: output, Error: err.Error(), Steps: steps, Ms: time.Since(t0).Seconds() * 1000}
			}
			push(r)
		case "UNARY_NEG":
			f, _ := asFloat(pop())
			push(-f)
		case "UNARY_NOT":
			push(!truthy(pop()))
		case "UNARY_LEN":
			v := pop()
			switch x := v.(type) {
			case string:
				push(float64(len(x)))
			case []interface{}:
				push(float64(len(x)))
			default:
				push(0.0)
			}
		case "BUILD_LIST":
			n := argInt(ins.Arg)
			items := make([]interface{}, n)
			for i := n - 1; i >= 0; i-- {
				items[i] = pop()
			}
			push(items)
		case "GET_ITEM":
			idx, xs := pop(), pop()
			i, _ := asFloat(idx)
			switch x := xs.(type) {
			case []interface{}:
				push(x[int(i)])
			default:
				return Result{OK: false, Output: output, Error: "get_item", Steps: steps, Ms: time.Since(t0).Seconds() * 1000}
			}
		case "JUMP":
			ip = argInt(ins.Arg)
		case "JUMP_IF_FALSE":
			if !truthy(pop()) {
				ip = argInt(ins.Arg)
			}
		case "PRINT":
			v := pop()
			if f, ok := asFloat(v); ok && f == float64(int64(f)) {
				output = append(output, fmt.Sprintf("%d", int64(f)))
			} else {
				output = append(output, fmt.Sprint(v))
			}
		case "POP":
			pop()
		case "RETURN":
			return Result{OK: true, Output: output, Value: pop(), Steps: steps, Ms: time.Since(t0).Seconds() * 1000}
		default:
			return Result{OK: false, Output: output, Error: "unknown op " + ins.Op, Steps: steps, Ms: time.Since(t0).Seconds() * 1000}
		}
	}
	return Result{OK: true, Output: output, Steps: steps, Ms: time.Since(t0).Seconds() * 1000}
}

func main() {
	var data []byte
	var err error
	if len(os.Args) > 1 {
		data, err = os.ReadFile(os.Args[1])
	} else {
		data, err = io.ReadAll(os.Stdin)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "%v\n", err)
		os.Exit(1)
	}
	var code CodeObject
	if err := json.Unmarshal(data, &code); err != nil {
		fmt.Fprintf(os.Stderr, "%v\n", err)
		os.Exit(1)
	}
	res := run(code, 50000000)
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(res)
	if !res.OK {
		os.Exit(1)
	}
}
