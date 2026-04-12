#!/usr/bin/env python3
"""PDF Processing Pipeline for Claude Chat

Uploads PDFs to Anthropic's Files API then runs an interactive
multi-turn chat with all documents available for analysis.
Prompt caching keeps costs low across repeated queries — documents
are sent once and cached; follow-up turns only pay for new tokens.

Setup:
    cd pdf_pipeline
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...

Usage:
    1. Drop PDF files into pdfs/
    2. python pipeline.py

Commands inside the chat:
    /list   show loaded documents and their file IDs
    /quit   exit
"""

import anthropic
import json
import os
import sys
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

PDF_DIR = Path(__file__).parent / "pdfs"
REGISTRY_FILE = Path(__file__).parent / "registry.json"
MODEL = "claude-opus-4-6"

# ── Registry helpers ───────────────────────────────────────────────────────────


def load_registry() -> dict[str, str]:
    """Load the filename → file_id mapping from disk."""
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    return {}


def save_registry(registry: dict[str, str]) -> None:
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


# ── PDF sync ───────────────────────────────────────────────────────────────────


def sync_pdfs(client: anthropic.Anthropic, registry: dict[str, str]) -> dict[str, str]:
    """Upload any new PDFs from pdfs/ to the Files API; skip already-uploaded ones."""
    PDF_DIR.mkdir(exist_ok=True)
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"\nNo PDFs found. Drop files into: {PDF_DIR.absolute()}")
        return registry

    print(f"\nSyncing {len(pdf_files)} PDF(s)...")

    for pdf_path in pdf_files:
        name = pdf_path.name
        if name in registry:
            print(f"  • {name}  [cached: {registry[name]}]")
            continue

        print(f"  • {name}  uploading...", end=" ", flush=True)
        try:
            with open(pdf_path, "rb") as f:
                result = client.beta.files.upload(
                    file=(name, f, "application/pdf"),
                )
            registry[name] = result.id
            save_registry(registry)
            print(f"done [{result.id}]")
        except Exception as e:
            print(f"failed: {e}")

    return registry


# ── Chat helpers ───────────────────────────────────────────────────────────────


def build_first_turn_content(registry: dict[str, str], question: str) -> list:
    """
    Build the first-turn content blocks: all documents + the user's question.

    cache_control on the last document caches the entire document prefix so
    subsequent turns skip re-sending those tokens (saves ~90 % on docs).
    A 1-hour TTL keeps the cache alive across a longer session.
    """
    items = list(registry.items())
    blocks: list[dict] = []

    for i, (name, file_id) in enumerate(items):
        block: dict = {
            "type": "document",
            "source": {"type": "file", "file_id": file_id},
            "title": Path(name).stem.replace("_", " ").replace("-", " ").title(),
        }
        if i == len(items) - 1:
            # Cache everything up through the last document
            block["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
        blocks.append(block)

    blocks.append({"type": "text", "text": question})
    return blocks


def show_usage(usage) -> None:
    parts = [f"in={usage.input_tokens}", f"out={usage.output_tokens}"]
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    if cache_read:
        parts.append(f"cache_read={cache_read}")
    if cache_write:
        parts.append(f"cache_write={cache_write}")
    print(f"\n  [tokens: {', '.join(parts)}]\n")


# ── Chat loop ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are an expert document analyst. Answer questions based solely on the "
    "provided PDF documents. Cite the relevant document title and section "
    "whenever you reference specific information. If the answer is not in the "
    "documents, say so clearly."
)


def run_chat(client: anthropic.Anthropic, registry: dict[str, str]) -> None:
    print(f"\n{'─' * 60}")
    print(" PDF Analysis Chat  |  multi-document Q&A with Claude")
    print(f"{'─' * 60}")
    print(f" {len(registry)} document(s) loaded:")
    for name in registry:
        print(f"   • {name}")
    print(f"\n Commands: /list   /quit")
    print(f"{'─' * 60}\n")

    messages: list[dict] = []
    documents_embedded = False

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit"):
            print("Goodbye!")
            break

        if user_input.lower() == "/list":
            print()
            for name, fid in registry.items():
                print(f"  • {name}  [{fid}]")
            print()
            continue

        # First message: embed all document blocks so the API can cache them.
        # Follow-up messages: send plain text — the document prefix is served
        # from cache at ~10 % of the normal input-token cost.
        if not documents_embedded:
            content = build_first_turn_content(registry, user_input)
            documents_embedded = True
        else:
            content = user_input

        messages.append({"role": "user", "content": content})
        print("\nClaude: ", end="", flush=True)

        response_text = ""
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=8096,
                system=SYSTEM_PROMPT,
                messages=messages,
                extra_headers={"anthropic-beta": "files-api-2025-04-14"},
            ) as stream:
                for chunk in stream.text_stream:
                    print(chunk, end="", flush=True)
                    response_text += chunk
                final = stream.get_final_message()

            show_usage(final.usage)
            messages.append({"role": "assistant", "content": response_text})

        except anthropic.BadRequestError as e:
            print(f"\nRequest error: {e.message}\n")
            messages.pop()
        except anthropic.RateLimitError:
            print("\nRate limited — please wait a moment and retry.\n")
            messages.pop()
        except anthropic.APIError as e:
            print(f"\nAPI error: {e}\n")
            messages.pop()


# ── Entry point ────────────────────────────────────────────────────────────────


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    client = anthropic.Anthropic()

    print("Terra Balance — PDF Analysis Pipeline")

    registry = load_registry()
    registry = sync_pdfs(client, registry)

    if not registry:
        print("No documents loaded. Exiting.")
        sys.exit(0)

    run_chat(client, registry)


if __name__ == "__main__":
    main()
