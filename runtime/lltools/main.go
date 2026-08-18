// lltools — Go local tool runner + optional HTTP daemon + LLM HTTP.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

type ToolCall struct {
	Name string                 `json:"name"`
	Args map[string]interface{} `json:"args"`
}
type ToolResult struct {
	Name   string      `json:"name"`
	OK     bool        `json:"ok"`
	Result interface{} `json:"result,omitempty"`
	Error  string      `json:"error,omitempty"`
	Ms     float64     `json:"ms"`
}
type BatchRequest struct {
	Tools    []ToolCall `json:"tools"`
	Parallel bool       `json:"parallel"`
}
type BatchResponse struct {
	OK      bool         `json:"ok"`
	Results []ToolResult `json:"results"`
	Ms      float64      `json:"ms"`
	Runtime string       `json:"runtime"`
}

func strArg(args map[string]interface{}, key, def string) string {
	if v, ok := args[key]; ok && v != nil {
		return fmt.Sprint(v)
	}
	return def
}

func runTool(tc ToolCall) ToolResult {
	t0 := time.Now()
	res := ToolResult{Name: tc.Name}
	defer func() { res.Ms = time.Since(t0).Seconds() * 1000 }()
	switch tc.Name {
	case "now":
		res.OK = true
		res.Result = map[string]interface{}{"iso": time.Now().UTC().Format(time.RFC3339Nano), "unix": time.Now().Unix()}
	case "word_length":
		text := strArg(tc.Args, "text", "")
		res.OK = true
		res.Result = map[string]interface{}{"text": text, "length": len(text), "words": len(strings.Fields(text))}
	case "read_file":
		path := strArg(tc.Args, "path", "")
		b, err := os.ReadFile(path)
		if err != nil {
			res.Error = err.Error()
			return res
		}
		res.OK = true
		res.Result = map[string]interface{}{"path": path, "bytes": len(b), "content": string(b)}
	case "write_file":
		path := strArg(tc.Args, "path", "")
		content := strArg(tc.Args, "content", "")
		_ = os.MkdirAll(filepath.Dir(path), 0755)
		if err := os.WriteFile(path, []byte(content), 0644); err != nil {
			res.Error = err.Error()
			return res
		}
		res.OK = true
		res.Result = map[string]interface{}{"path": path, "bytes": len(content)}
	case "list_dir":
		path := strArg(tc.Args, "path", ".")
		entries, err := os.ReadDir(path)
		if err != nil {
			res.Error = err.Error()
			return res
		}
		names := []string{}
		for _, e := range entries {
			names = append(names, e.Name())
		}
		res.OK = true
		res.Result = map[string]interface{}{"path": path, "entries": names}
	case "project_stats":
		root := strArg(tc.Args, "path", ".")
		var files, dirs int
		var nbytes int64
		_ = filepath.Walk(root, func(p string, info os.FileInfo, err error) error {
			if err != nil {
				return nil
			}
			if info.IsDir() {
				if strings.Contains(p, ".git") || strings.Contains(p, "__pycache__") {
					return filepath.SkipDir
				}
				dirs++
				return nil
			}
			files++
			nbytes += info.Size()
			return nil
		})
		res.OK = true
		res.Result = map[string]interface{}{"path": root, "files": files, "dirs": dirs, "bytes": nbytes}
	case "search_code":
		root := strArg(tc.Args, "path", ".")
		query := strArg(tc.Args, "query", "")
		matches := []map[string]interface{}{}
		_ = filepath.Walk(root, func(p string, info os.FileInfo, err error) error {
			if err != nil || info.IsDir() {
				if info != nil && info.IsDir() && (strings.Contains(p, ".git") || strings.Contains(p, "node_modules")) {
					return filepath.SkipDir
				}
				return nil
			}
			if len(matches) >= 20 {
				return fmt.Errorf("done")
			}
			ext := filepath.Ext(p)
			if ext != ".py" && ext != ".go" && ext != ".ll" && ext != ".md" && ext != ".js" {
				return nil
			}
			b, err := os.ReadFile(p)
			if err != nil {
				return nil
			}
			if query != "" && strings.Contains(string(b), query) {
				matches = append(matches, map[string]interface{}{"file": p, "query": query})
			}
			return nil
		})
		res.OK = true
		res.Result = map[string]interface{}{"query": query, "matches": matches, "count": len(matches)}
	default:
		res.Error = "unknown tool: " + tc.Name
	}
	return res
}

func runBatch(req BatchRequest) BatchResponse {
	t0 := time.Now()
	out := BatchResponse{Runtime: "go-lltools"}
	if !req.Parallel || len(req.Tools) <= 1 {
		for _, tc := range req.Tools {
			out.Results = append(out.Results, runTool(tc))
		}
	} else {
		var mu sync.Mutex
		var wg sync.WaitGroup
		out.Results = make([]ToolResult, len(req.Tools))
		for i, tc := range req.Tools {
			wg.Add(1)
			go func(i int, tc ToolCall) {
				defer wg.Done()
				r := runTool(tc)
				mu.Lock()
				out.Results[i] = r
				mu.Unlock()
			}(i, tc)
		}
		wg.Wait()
	}
	out.OK = true
	for _, r := range out.Results {
		if !r.OK {
			out.OK = false
			break
		}
	}
	out.Ms = time.Since(t0).Seconds() * 1000
	return out
}

func main() {
	daemon := flag.String("daemon", "", "listen addr e.g. 127.0.0.1:9876")
	flag.Parse()
	if *daemon != "" {
		http.HandleFunc("/tools", func(w http.ResponseWriter, r *http.Request) {
			body, _ := io.ReadAll(r.Body)
			var req BatchRequest
			if err := json.Unmarshal(body, &req); err != nil {
				http.Error(w, err.Error(), 400)
				return
			}
			res := runBatch(req)
			w.Header().Set("Content-Type", "application/json")
			_ = json.NewEncoder(w).Encode(res)
		})
		http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte(`{"ok":true,"runtime":"go-lltools"}`))
		})
		fmt.Println("lltools daemon on", *daemon)
		_ = http.ListenAndServe(*daemon, nil)
		return
	}
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	var req BatchRequest
	if err := json.Unmarshal(data, &req); err != nil {
		var tc ToolCall
		_ = json.Unmarshal(data, &tc)
		req.Tools = []ToolCall{tc}
	}
	res := runBatch(req)
	_ = json.NewEncoder(os.Stdout).Encode(res)
}
