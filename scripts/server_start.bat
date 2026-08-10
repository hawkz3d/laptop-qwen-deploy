@echo off
cd /d <LLAMA_DIR>
llama-server.exe -m <MODELS_DIR>\ornith-1.0-35b-Q4_K_M.gguf -ngl 999 -ot exps=CPU --no-mmap --no-kv-offload -ctk q8_0 -ctv q8_0 -c 32768 --jinja --host 0.0.0.0 --port 8080 > <LLAMA_DIR>\server.log 2>&1
