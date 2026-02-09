import subprocess
import requests
import re
from pathlib import Path
import platform

# =========================
# Configuration
# =========================

MODEL = "gpt-oss:20b"   # replaceable

BASE_DIR = Path.cwd().resolve()

SYSTEM_PROMPT = f"""You are a local coding agent operating in a read-only, inspection-only mode.

The current project folder is:
{BASE_DIR}

!!!CRITICAL: Always check the COMMAND_REQUEST section carefully. Respond only in the specified format with no additional text or commands. Do not guess or invent commands.

=========================
CAPABILITIES
You may inspect directory listings and file contents.
You may NOT modify, create, delete, or rename files.
You may NOT install software, run network tools, or execute commands directly.
=========================
ENVIRONMENT
Operating system: Windows
Shell: Windows Command Prompt (cmd.exe)
Path separator: backslash
=========================
FUNDAMENTAL CONSTRAINTS
You have NO direct filesystem or shell access.
You can ONLY reason from OBSERVATION blocks.
Any text prefixed with "OBSERVATION:" is authoritative ground truth.
Never guess file contents; do not invent files or folders.
Never assume write permissions.
You must NOT execute or attempt to run commands; only request inspection commands.
=========================
RESPONSE PROTOCOL (STRICT)
Use ONE of the following modes:

MODE 1 — INSPECTION REQUIRED
Use when you need to see files or directories. In this mode, you are allowed to generate a command prompt output.

Output format (EXACTLY):
"COMMAND_REQUEST: <command>"

Examples:
COMMAND_REQUEST: type myfile.py
COMMAND_REQUEST: dir /b
COMMAND_REQUEST: type src\main.py

Rules:

Always respond ONLY with the command in the specified format.
NO explanations, NO extra text, NO additional commands.
If multiple commands could be used, choose the simplest that provides sufficient information.
MODE 2 — FINAL ANSWER
Use when you have enough information to answer the user's question.

Output format:

Provide a concise, direct answer in 1-3 sentences.
NO analysis, NO commentary, NO formatting headers.
CRITICAL: If inspection is needed, request directory listing. Do not perform or suggest any command execution.

IMPORTANT:

Respond only in the specified format.
Never deviate or invent commands.
Always prioritize safety and read-only operations.
"""


# =========================
# Utilities
# =========================


def extract_command_request(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("COMMAND_REQUEST:"):
            return line[len("COMMAND_REQUEST:"):].strip()
    return None



def clean_model_text(text: str) -> str:
    """Remove any model-side tool artifacts or special tokens."""
    text = re.sub(r"<\|.*?\|>", "", text, flags=re.S)
    return text.strip()

def build_prompt(messages):
    parts = []
    for m in messages:
        role = m["role"].upper()
        parts.append(f"{role}:\n{m['content']}")
    return "\n\n".join(parts)

import time

def call_llm(messages):
    prompt = build_prompt(messages)

    proc = subprocess.Popen(
        ["ollama", "run", MODEL],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1
    )

    proc.stdin.write(prompt)
    proc.stdin.close()  # 🔑 signal EOF

    print("Agent> ", end="", flush=True)

    output = []

    for line in proc.stdout:
        print(line, end="", flush=True)
        output.append(line)

        

    proc.wait(timeout=5)
    return clean_model_text("".join(output))

def run_shell(command):


    print("\n⚠️  Agent wants to run (read-only):")
    print(f"> {command}")
    if input("Run it? [y/N]: ").lower().strip() != "y":
        return "Command not executed."

    result = subprocess.run(
        command,
        shell=True,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    return f"{result.stdout}{result.stderr}"

# =========================
# Controller Logic
# =========================

def needs_directory_listing(user_text: str) -> bool:
    triggers = [
        "review",
        "project folder",
        "this folder",
        "current folder",
        "list files",
        "directory"
    ]
    return any(t in user_text.lower() for t in triggers)

# =========================
# Main Loop (v1.2 Protocol)
# =========================

def main():
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    print("🧠 Local Coding Agent v1.2 (type 'exit' to quit)\n")

    while True:
        user = input("You> ")
        if user.lower() in ("exit", "quit"):
            break

        # Step 1 — User input
        messages.append({"role": "user", "content": user})

        # Step 2 — Controller decides observation
        observation = None
        if needs_directory_listing(user):
            print("[SHELL] dir")
            output = run_shell("dir")
            observation = (
                "OBSERVATION:\n"
                "Shell directory listing (authoritative):\n"
                + output
            )

        # Step 3 — Construct reasoning context
        context = [messages[0]]  # system prompt
        context.append({"role": "user", "content": user})

        if observation:
            context.append({"role": "system", "content": observation})
            context.append({
                "role": "user",
                "content": "Based only on the observation above, respond to the original request."
            })

        while True:
            reply = clean_model_text(call_llm(context))
            print("\n")  # add newline after streaming output
            #print("Agent reply", reply)
            cmd = extract_command_request(reply)
            if not cmd:
                break  # no more inspection needed

            output = run_shell(cmd)

            context.append({
                "role": "system",
                "content": (
                    "OBSERVATION:\n"
                    f"Result of `{cmd}`:\n"
                    + output
                )
            })

        messages.append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    main()