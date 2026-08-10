@echo off
cd /d <MODELS_DIR>
curl -L --connect-timeout 15 -C - -sS -o <MODELS_DIR>\ornith-1.0-35b-Q4_K_M.gguf https://hf-mirror.com/deepreinforce-ai/Ornith-1.0-35B-GGUF/resolve/main/ornith-1.0-35b-Q4_K_M.gguf
echo EXIT_CODE=%ERRORLEVEL% TIME=%DATE% %TIME% >> <MODELS_DIR>\dl_log.txt
