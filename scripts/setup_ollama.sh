#!/bin/bash
# 启动3个Ollama实例

echo "启动 Architect Agent (端口 11434)..."
OLLAMA_HOST=127.0.0.1:11434 ollama serve &
ARCH_PID=$!
sleep 3

echo "启动 Developer Agent (端口 11435)..."
OLLAMA_HOST=127.0.0.1:11435 ollama serve &
DEV_PID=$!
sleep 3

echo "启动 QA Agent (端口 11436)..."
OLLAMA_HOST=127.0.0.1:11436 ollama serve &
QA_PID=$!
sleep 3

echo "预加载模型..."
curl -s http://localhost:11434/api/generate -d '{"model":"qwen2.5:3b","keep_alive":-1,"prompt":"hello"}' > /dev/null
curl -s http://localhost:11435/api/generate -d '{"model":"qwen2.5:3b","keep_alive":-1,"prompt":"hello"}' > /dev/null
curl -s http://localhost:11436/api/generate -d '{"model":"qwen2.5:3b","keep_alive":-1,"prompt":"hello"}' > /dev/null

echo "✅ 所有Agent已就绪！"
echo "进程ID: Architect=$ARCH_PID, Developer=$DEV_PID, QA=$QA_PID"
echo "使用 'pkill ollama' 来停止所有实例"