---
name: peek-thinking
description: Observe another Claude Code instance's thinking process and tool orchestration. Use when user wants to watch how another model thinks, compare different models, debug AI decision-making, or test different settings configs. Triggers on phrases like "观察思考过程", "看它怎么想", "另一个模型的思考", "peek thinking", "observe model", "debug AI decisions".
---

# Peek Thinking

Launch another Claude Code instance with full thinking capture.

## Core Command

```bash
echo "<prompt>" | claude --settings <config.json> --print \
  --output-format=stream-json --include-partial-messages --verbose
```

This captures:
- **Thinking blocks** (`type: "thinking"`, `thinking_delta`) — the model's internal reasoning
- **Tool calls** (`type: "tool_use"`) — what tools it invokes
- **Messages** (`type: "assistant"`) — final responses
- **Hook events** — session lifecycle

## Output Structure

The stream produces JSON events:

```json
{"type":"content_block_start","content_block":{"type":"thinking"}}
{"type":"stream_event","event":{"delta":{"type":"thinking_delta","thinking":"用户让我..."}}
{"type":"stream_event","event":{"delta":{"type":"thinking_delta","thinking":"这是一个简单..."}}
{"type":"assistant","message":{"content":[{"type":"thinking","thinking":"完整思考内容"}]}}
```

## Usage Patterns

### Quick peek (single prompt)

```bash
echo "简短介绍自己" | claude --settings .claude/qwen.json --print \
  --output-format=stream-json --include-partial-messages --verbose 2>&1 | head -100
```

### Extract thinking only

```bash
echo "<prompt>" | claude --settings <config> --print \
  --output-format=stream-json --include-partial-messages --verbose 2>&1 \
  | grep 'thinking_delta' | jq -r '.event.delta.thinking' | tr -d '\n'
```

### Full capture to file

```bash
echo "<prompt>" | claude --settings <config> --print \
  --output-format=stream-json --include-partial-messages --verbose \
  > /tmp/thinking_capture.json 2>&1
```

### Multi-turn conversation

Use `--input-format=stream-json` for structured multi-turn input:

```bash
cat input.json | claude --settings <config> --print \
  --input-format=stream-json --output-format=stream-json \
  --include-partial-messages --verbose
```

## Analyzing Results

After capture, use jq to extract specific parts:

```bash
# All thinking content
cat capture.json | jq -r 'select(.type=="stream_event" and .event.delta.type=="thinking_delta") | .event.delta.thinking'

# Tool calls
cat capture.json | jq 'select(.type=="stream_event" and .event.content_block.type=="tool_use")'

# Final message
cat capture.json | jq 'select(.type=="assistant") | .message.content'
```

## Settings File Format

The settings file specifies the alternate model:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.example.com/anthropic",
    "ANTHROPIC_MODEL": "model-id",
    "ANTHROPIC_AUTH_TOKEN": "token"
  }
}
```

## Workflow

1. User provides prompt + settings file path
2. Run capture command
3. Parse and present thinking content to user
4. Optionally analyze tool orchestration patterns

## Tips

- Use `2>&1` to merge stderr (hook events) with stdout
- Pipe through `head` for quick preview, full capture for analysis
- The `--verbose` flag is required for `stream-json` format
- Thinking is streamed token-by-token via `thinking_delta` events