#!/usr/bin/env python3
"""File-based orchestrator for the water bottle prompt/review agents."""

from __future__ import annotations

import argparse
import fcntl
import json
import re
import shutil
import os
import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
JACKY_ROOT = ROOT.parent
PROMPT_AGENT = JACKY_ROOT / "waterbottle-prompt-agent" / "AGENTS.md"
REVIEW_AGENT = JACKY_ROOT / "waterbottle-review-agent" / "AGENTS.md"
RUNS_DIR = ROOT / "runs"


MAIN_SLOTS = [
    ("main_1", "主图1 / Hero image"),
    ("main_2", "主图2 / Core selling point"),
    ("main_3", "主图3 / Detail or structure"),
    ("main_4", "主图4 / Scene image"),
    ("main_5", "主图5 / White background image"),
]

DETAIL_SLOT_COUNTS = {
    "taobao": 8,
    "淘宝": 8,
    "1688": 10,
}

IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]
PROMPT_EXTENSIONS = [".md", ".txt"]
HUMAN_DECISIONS = {
    "accept": "accepted_by_human",
    "review": "needs_review_agent",
    "regenerate": "needs_regeneration",
    "revise-prompt": "needs_prompt_revision",
    "reject": "rejected_by_human",
}
MASTER_DECISIONS = HUMAN_DECISIONS


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "waterbottle"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_or_reference(paths: list[str], dest_dir: Path) -> list[dict[str, str]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for index, raw in enumerate(paths, start=1):
        src = Path(raw).expanduser()
        record = {"id": f"source_{index}", "path": str(src)}
        if src.exists() and src.is_file():
            copied = dest_dir / f"{index:02d}-{src.name}"
            shutil.copy2(src, copied)
            record["copied_path"] = str(copied)
        else:
            record["missing"] = "true"
        records.append(record)
    return records


def slot_plan(platform: str) -> list[dict[str, str]]:
    normalized = platform.lower()
    details = DETAIL_SLOT_COUNTS.get(normalized, DETAIL_SLOT_COUNTS.get(platform, 8))
    slots = [
        {"id": slot_id, "kind": "main", "title": title, "status": "needs_prompt"}
        for slot_id, title in MAIN_SLOTS
    ]
    for i in range(1, details + 1):
        slots.append(
            {
                "id": f"detail_{i}",
                "kind": "detail",
                "title": f"详情图{i} / Detail image {i}",
                "status": "needs_prompt",
            }
        )
    return slots


def run_path(run: str) -> Path:
    path = Path(run)
    if not path.is_absolute():
        path = RUNS_DIR / run
    if not path.exists():
        raise SystemExit(f"Run not found: {path}")
    return path


def load_state(run_dir: Path) -> dict[str, Any]:
    return read_json(run_dir / "state.json")


def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    write_json(run_dir / "state.json", state)


@contextmanager
def state_transaction(run_dir: Path):
    lock_path = run_dir / ".state.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load_state(run_dir)
        yield state
        save_state(run_dir, state)
        fcntl.flock(lock, fcntl.LOCK_UN)


def find_slot(state: dict[str, Any], slot_id: str) -> dict[str, Any]:
    for slot in state["slots"]:
        if slot["id"] == slot_id:
            return slot
    raise SystemExit(f"Slot not found: {slot_id}")


def slot_dir(run_dir: Path, slot_id: str) -> Path:
    return run_dir / "02_slots" / slot_id


def masters_dir(run_dir: Path) -> Path:
    return run_dir / "01_masters"


def master_dir(run_dir: Path, master_id: str) -> Path:
    return masters_dir(run_dir) / master_id


def find_named_file(directory: Path, stem: str, extensions: list[str]) -> Path | None:
    for ext in extensions:
        candidate = directory / f"{stem}{ext}"
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def is_image_path(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def markdown_path_candidates(text: str) -> list[Path]:
    candidates = []
    patterns = [
        r"`([^`]+\.(?:png|jpg|jpeg|webp))`",
        r"(?<![\w/.-])(/[^`\s]+\.(?:png|jpg|jpeg|webp))",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            candidates.append(Path(match.group(1)).expanduser())
    return candidates


def source_list_markdown(sources: list[dict[str, str]]) -> str:
    lines = []
    for src in sources:
        path = src.get("copied_path") or src["path"]
        lines.append(f"- {src['id']}: `{path}`")
    return "\n".join(lines)


def role_agent_path(state: dict[str, Any], role: str) -> Path:
    if role == "prompt":
        return Path(state["prompt_agent"])
    if role == "review":
        return Path(state["review_agent"])
    raise SystemExit(f"Unknown agent role: {role}")


def build_agent_prompt(state: dict[str, Any], role: str, task_path: Path) -> str:
    agent_path = role_agent_path(state, role)
    if not agent_path.exists():
        raise SystemExit(f"Missing {role} agent prompt: {agent_path}")
    if not task_path.exists():
        raise SystemExit(f"Missing task file: {task_path}")
    agent_prompt = agent_path.read_text(encoding="utf-8")
    task_text = task_path.read_text(encoding="utf-8")
    return f"""You are being invoked as the local `{role}` agent.

Follow this agent behavior definition exactly:

```markdown
{agent_prompt}
```

Run this task:

```markdown
{task_text}
```

Important execution constraints:
- Do not edit files.
- Do not run shell commands.
- Return only the requested agent output for the task.
- If the task asks for markdown, return markdown only.
- If the task asks for JSON, return JSON only.
"""


def source_image_paths(state: dict[str, Any]) -> list[Path]:
    paths = []
    for source in state.get("sources", []):
        raw = source.get("copied_path") or source.get("path")
        if not raw:
            continue
        path = Path(raw).expanduser()
        if path.exists() and path.is_file() and is_image_path(path):
            paths.append(path)
    return paths


def agent_image_paths(state: dict[str, Any], role: str, task_path: Path) -> list[Path]:
    text = task_path.read_text(encoding="utf-8")
    seen = set()
    images = []
    for path in markdown_path_candidates(text):
        if path.exists() and path.is_file() and is_image_path(path) and path not in seen:
            images.append(path)
            seen.add(path)
    if role in {"prompt", "review"}:
        for path in source_image_paths(state):
            if path not in seen:
                images.append(path)
                seen.add(path)
    return images


def default_agent_output_path(task_path: Path) -> Path:
    return task_path.with_name(f"{task_path.stem}_agent_output.md")


def build_agent_command(backend: str, output_path: Path, image_paths: list[Path]) -> list[str]:
    if backend == "codex":
        command = [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "-C",
            str(ROOT),
            "--sandbox",
            "read-only",
            "--output-last-message",
            str(output_path),
        ]
        for image in image_paths:
            command.extend(["--image", str(image)])
        command.append("-")
        return command
    if backend == "hermes":
        command = ["hermes", "chat", "-Q"]
        for image in image_paths:
            command.extend(["--image", str(image)])
        return command
    raise SystemExit(f"Unknown backend: {backend}")


def run_local_agent(
    state: dict[str, Any],
    role: str,
    task_path: Path,
    output_path: Path,
    backend: str,
    include_images: bool,
    dry_run: bool = False,
) -> list[str]:
    prompt = build_agent_prompt(state, role, task_path)
    image_paths = agent_image_paths(state, role, task_path) if include_images else []
    command = build_agent_command(backend, output_path, image_paths)
    if dry_run:
        return command
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if backend == "codex":
        result = subprocess.run(command, input=prompt, text=True, capture_output=True)
        if result.returncode != 0:
            raise SystemExit(result.stderr or result.stdout or f"Agent command failed: {command}")
        if not output_path.exists():
            write_text(output_path, result.stdout)
        return command
    if backend == "hermes":
        result = subprocess.run(command + ["-q", prompt], text=True, capture_output=True)
        if result.returncode != 0:
            raise SystemExit(result.stderr or result.stdout or f"Agent command failed: {command}")
        write_text(output_path, result.stdout)
        return command
    raise SystemExit(f"Unknown backend: {backend}")


def select_sources(state: dict[str, Any], source_ids: list[str]) -> list[dict[str, str]]:
    by_id = {src["id"]: src for src in state["sources"]}
    selected = []
    for source_id in source_ids:
        if source_id not in by_id:
            raise SystemExit(f"Unknown source id in master plan: {source_id}")
        selected.append(by_id[source_id])
    return selected


def load_master_plan(run_dir: Path) -> list[dict[str, Any]]:
    path = masters_dir(run_dir) / "master_plan.json"
    if not path.exists():
        raise SystemExit(f"Missing master plan: {path}")
    data = read_json(path)
    masters = data.get("masters")
    if not isinstance(masters, list) or not masters:
        raise SystemExit(f"Master plan must contain a non-empty 'masters' list: {path}")
    seen = set()
    for master in masters:
        master_id = master.get("id")
        if not master_id or not re.match(r"^[a-z0-9_ -]+$", master_id):
            raise SystemExit(f"Invalid master id: {master_id!r}")
        normalized = slugify(master_id).replace("-", "_")
        master["id"] = normalized
        if normalized in seen:
            raise SystemExit(f"Duplicate master id: {normalized}")
        seen.add(normalized)
        master.setdefault("title", normalized)
        master.setdefault("purpose", "")
        master.setdefault("primary_sources", [])
        master.setdefault("secondary_sources", [])
        master.setdefault("serves_slots", [])
        master.setdefault("sku", "")
        master.setdefault("state", "")
        master.setdefault("angle", "")
        master.setdefault("notes", "")
    return masters


def find_master(run_dir: Path, master_id: str) -> dict[str, Any]:
    normalized = slugify(master_id).replace("-", "_")
    for master in load_master_plan(run_dir):
        if master["id"] == normalized:
            return master
    raise SystemExit(f"Master not found in master plan: {master_id}")


def source_classification_task_text(state: dict[str, Any]) -> str:
    return f"""# Task For Prompt Agent: Source Image Classification

Use system prompt:
`{state['prompt_agent']}`

Platform: `{state['platform']}`

Source photos:
{source_list_markdown(state['sources'])}

Classify every uploaded source image before any image generation.

Return only a structured markdown report with these sections:

1. Source Image Classification
   - For each `source_N`, identify SKU/color, angle, product state, visible parts, text visibility, and fidelity value.
2. State And Angle Coverage
   - Summarize which product states and angles are covered by the sources.
3. Master Candidates
   - Propose master candidates that should be generated before slot images.
   - For each candidate include id, title, purpose, primary source ids, secondary source ids, SKU, state, angle, and served slot ids.
4. Source Risks
   - Call out missing close-ups, conflicting states, weak text references, or SKU uncertainty.

Do not write final slot prompts yet.
"""


def master_plan_task_text(state: dict[str, Any], run_dir: Path) -> str:
    return f"""# Task For Prompt Agent: Build Product Master Plan

Use system prompt:
`{state['prompt_agent']}`

Platform: `{state['platform']}`

Source classification:
`{run_dir / '01_assets' / 'source_classification.md'}`

Shared assets:
- Product Fact Assets: `{run_dir / '01_assets' / 'product_fact_assets.md'}`
- Geometry Anchors: `{run_dir / '01_assets' / 'geometry_anchors.md'}`
- Product State Map: `{run_dir / '01_assets' / 'product_state_map.md'}`
- SKU Consistency Brief: `{run_dir / '01_assets' / 'sku_consistency_brief.md'}`

Create a JSON master plan only. Do not include markdown outside the JSON.

Schema:
```json
{{
  "masters": [
    {{
      "id": "front_closed_blue",
      "title": "Blue front closed full bottle",
      "purpose": "Reusable product geometry master for scene and white-background slots",
      "primary_sources": ["source_1"],
      "secondary_sources": ["source_2"],
      "serves_slots": ["main_2", "main_5"],
      "sku": "blue",
      "state": "closed lid, raised handle",
      "angle": "front",
      "notes": "Keep body slogan placement and transparent lower body accurate."
    }}
  ]
}}
```
"""


def master_task_text(state: dict[str, Any], run_dir: Path, master: dict[str, Any]) -> str:
    primary_sources = select_sources(state, master.get("primary_sources", []))
    secondary_sources = select_sources(state, master.get("secondary_sources", []))
    secondary = source_list_markdown(secondary_sources) if secondary_sources else "- none"
    return f"""# Task For Prompt Agent: Generate Product Master Prompt

Use system prompt:
`{state['prompt_agent']}`

Platform: `{state['platform']}`
Master: `{master['id']}` - {master.get('title', '')}
Purpose: {master.get('purpose', '')}
SKU: {master.get('sku', '')}
Product state: {master.get('state', '')}
Angle: {master.get('angle', '')}
Serves slots: {', '.join(master.get('serves_slots', [])) or 'not assigned'}

Primary source photos for this master:
{source_list_markdown(primary_sources)}

Secondary source photos, use only for missing facts:
{secondary}

Shared assets:
- Source Classification: `{run_dir / '01_assets' / 'source_classification.md'}`
- Product Fact Assets: `{run_dir / '01_assets' / 'product_fact_assets.md'}`
- Geometry Anchors: `{run_dir / '01_assets' / 'geometry_anchors.md'}`
- Product State Map: `{run_dir / '01_assets' / 'product_state_map.md'}`
- SKU Consistency Brief: `{run_dir / '01_assets' / 'sku_consistency_brief.md'}`

Instructions:
- Generate only one master prompt for this product state/angle.
- Treat primary source photos as strict geometry references, not style inspiration.
- Do not attach all source photos to the image-generation call.
- Preserve product geometry, functional parts, SKU color, transparent sections, scale marks, and required text placement.
- Output a ready-to-use image generation prompt for this master only.

Notes:
{master.get('notes', '')}
"""


def master_review_task_text(state: dict[str, Any], run_dir: Path, master: dict[str, Any], generated: str, prompt_path: Path) -> str:
    primary_sources = select_sources(state, master.get("primary_sources", []))
    secondary_sources = select_sources(state, master.get("secondary_sources", []))
    secondary = source_list_markdown(secondary_sources) if secondary_sources else "- none"
    return f"""# Task For Review Agent: Strict Product Master Review

Use system prompt:
`{state['review_agent']}`

Platform: `{state['platform']}`
Master: `{master['id']}` - {master.get('title', '')}
Purpose: {master.get('purpose', '')}
SKU: {master.get('sku', '')}
Product state: {master.get('state', '')}
Angle: {master.get('angle', '')}

Primary source photos:
{source_list_markdown(primary_sources)}

Secondary source photos:
{secondary}

Generated master image:
`{generated}`

Generation prompt used:
`{prompt_path}`

Shared assets:
- Source Classification: `{run_dir / '01_assets' / 'source_classification.md'}`
- Product Fact Assets: `{run_dir / '01_assets' / 'product_fact_assets.md'}`
- Geometry Anchors: `{run_dir / '01_assets' / 'geometry_anchors.md'}`
- Product State Map: `{run_dir / '01_assets' / 'product_state_map.md'}`
- SKU Consistency Brief: `{run_dir / '01_assets' / 'sku_consistency_brief.md'}`

Return PASS / REVISE / FAIL, scorecard, difference table, hard-fail checks, prompt defects, Corrective Prompt Delta, and a regeneration decision:

- `DIRECT_REGENERATE`: prompt is basically correct; regenerate same prompt or with tiny negative-prompt additions.
- `REVISE_PROMPT`: prompt is missing constraints or contains wrong instructions; revise prompt before generating.
- `REQUEST_MORE_SOURCE`: source photos/assets are insufficient for this master.
"""


def create_master_tasks(run_dir: Path, state: dict[str, Any]) -> int:
    count = 0
    for master in load_master_plan(run_dir):
        directory = master_dir(run_dir, master["id"])
        write_text(directory / "master_task.md", master_task_text(state, run_dir, master))
        write_json(
            directory / "master_state.json",
            {
                "id": master["id"],
                "status": "master_task_ready",
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            },
        )
        count += 1
    return count


def accepted_masters_for_slot(run_dir: Path, slot_id: str) -> list[dict[str, Any]]:
    masters = []
    for master in load_master_plan(run_dir):
        if slot_id not in master.get("serves_slots", []):
            continue
        directory = master_dir(run_dir, master["id"])
        state_path = directory / "master_state.json"
        generated_path = directory / "generated.json"
        if not state_path.exists() or not generated_path.exists():
            continue
        master_state = read_json(state_path)
        if master_state.get("status") not in {"accepted_by_human", "passed"}:
            continue
        item = dict(master)
        item["generated_image"] = read_json(generated_path).get("generated_image", "")
        masters.append(item)
    return masters


def create_slot_control_packet(run_dir: Path, state: dict[str, Any], slot_id: str) -> Path:
    slot = find_slot(state, slot_id)
    masters = accepted_masters_for_slot(run_dir, slot_id)
    if not masters:
        raise SystemExit(f"No accepted/passed master is assigned to slot: {slot_id}")
    primary = masters[0]
    secondary = masters[1:]
    lines = [
        f"# Slot Control Packet: {slot_id}",
        "",
        f"Platform: `{state['platform']}`",
        f"Slot: `{slot['id']}` - {slot['title']}",
        "",
        "## Primary Master",
        "",
        f"- Master: `{primary['id']}` - {primary.get('title', '')}",
        f"- Generated image: `{primary.get('generated_image', '')}`",
        f"- SKU: {primary.get('sku', '')}",
        f"- State: {primary.get('state', '')}",
        f"- Angle: {primary.get('angle', '')}",
        "",
        "## Secondary Masters",
        "",
    ]
    if secondary:
        for master in secondary:
            lines.append(f"- `{master['id']}`: `{master.get('generated_image', '')}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Generation Instructions",
            "",
            "- Use the primary master as the product geometry and SKU anchor.",
            "- Use secondary masters only for missing angle/state/detail facts.",
            "- Do not attach all source photos to the image-generation call.",
            "- Keep the slot goal and composition specific to this slot.",
            "- Preserve product identity, functional state, SKU color, and visible text only when this slot requires it.",
            "",
            "## Shared Assets For Text Reference Only",
            "",
            f"- Source Classification: `{run_dir / '01_assets' / 'source_classification.md'}`",
            f"- Geometry Anchors: `{run_dir / '01_assets' / 'geometry_anchors.md'}`",
            f"- Product State Map: `{run_dir / '01_assets' / 'product_state_map.md'}`",
            f"- SKU Consistency Brief: `{run_dir / '01_assets' / 'sku_consistency_brief.md'}`",
            "",
        ]
    )
    out = slot_dir(run_dir, slot_id) / "slot_control_packet.md"
    write_text(out, "\n".join(lines))
    return out


def prompt_task_text(state: dict[str, Any], run_dir: Path, slot: dict[str, str]) -> str:
    return f"""# Task For Prompt Agent: Generate One Slot Prompt

Use system prompt:
`{state['prompt_agent']}`

Platform: `{state['platform']}`
Slot: `{slot['id']}` - {slot['title']}

Source photos:
{source_list_markdown(state['sources'])}

Shared assets:
- Product Fact Assets: `{run_dir / '01_assets' / 'product_fact_assets.md'}`
- Geometry Anchors: `{run_dir / '01_assets' / 'geometry_anchors.md'}`
- Product State Map: `{run_dir / '01_assets' / 'product_state_map.md'}`
- SKU Consistency Brief: `{run_dir / '01_assets' / 'sku_consistency_brief.md'}`

Instructions:
- Generate only this one slot prompt.
- If this is a main image, include `Generation call` and require one standalone image only.
- Copy concrete Geometry Anchors into the prompt.
- Include product identity lock, state lock, part asset lock, SKU lock when relevant.
- Do not generate prompts for other slots.
"""


def review_task_text(state: dict[str, Any], run_dir: Path, slot: dict[str, str], generated: str, prompt_path: Path) -> str:
    return f"""# Task For Review Agent: Strict Image Review

Use system prompt:
`{state['review_agent']}`

Platform: `{state['platform']}`
Slot: `{slot['id']}` - {slot['title']}

Source photos:
{source_list_markdown(state['sources'])}

Generated image:
`{generated}`

Generation prompt used:
`{prompt_path}`

Shared assets:
- Product Fact Assets: `{run_dir / '01_assets' / 'product_fact_assets.md'}`
- Geometry Anchors: `{run_dir / '01_assets' / 'geometry_anchors.md'}`
- Product State Map: `{run_dir / '01_assets' / 'product_state_map.md'}`
- SKU Consistency Brief: `{run_dir / '01_assets' / 'sku_consistency_brief.md'}`

Return PASS / REVISE / FAIL, scorecard, difference table, hard-fail checks, prompt defects, Corrective Prompt Delta, and a regeneration decision:

- `DIRECT_REGENERATE`: prompt is basically correct; regenerate same prompt or with tiny negative-prompt additions.
- `REVISE_PROMPT`: prompt is missing constraints or contains wrong instructions; revise prompt before generating.
- `REQUEST_MORE_SOURCE`: source photos/assets are insufficient; request close-up/dimensions/state reference first.
"""


def cmd_init(args: argparse.Namespace) -> None:
    run_name = f"{now_id()}-{slugify(args.name)}"
    run_dir = RUNS_DIR / run_name
    sources = copy_or_reference(args.source, run_dir / "00_inputs" / "source_photos")
    state = {
        "name": args.name,
        "platform": args.platform,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt_agent": str(PROMPT_AGENT),
        "review_agent": str(REVIEW_AGENT),
        "sources": sources,
        "slots": slot_plan(args.platform),
    }
    save_state(run_dir, state)
    write_text(run_dir / "01_assets" / "source_classification.md", "# Source Classification\n\n待由 prompt-agent 生成或粘贴。\n")
    write_text(run_dir / "01_assets" / "product_fact_assets.md", "# Product Fact Assets\n\n待由 prompt-agent 生成或粘贴。\n")
    write_text(run_dir / "01_assets" / "geometry_anchors.md", "# Geometry Anchors\n\n待由 prompt-agent 生成或粘贴。\n")
    write_text(run_dir / "01_assets" / "product_state_map.md", "# Product State Map\n\n待由 prompt-agent 生成或粘贴。\n")
    write_text(run_dir / "01_assets" / "sku_consistency_brief.md", "# SKU Consistency Brief\n\n待由 prompt-agent 生成或粘贴。\n")
    write_text(run_dir / "README.md", run_readme(state, run_name))
    write_text(run_dir / "01_prompt_agent" / "asset_extraction_task.md", asset_extraction_task(state))
    print(f"Created run: {run_dir}")
    print(f"Next: open {run_dir / '01_prompt_agent' / 'asset_extraction_task.md'}")


def run_readme(state: dict[str, Any], run_name: str) -> str:
    return f"""# Water Bottle Run: {state['name']}

Run ID: `{run_name}`
Platform: `{state['platform']}`

## Flow

1. Send `01_prompt_agent/asset_extraction_task.md` to the prompt agent.
2. Paste returned Product Fact Assets / Geometry Anchors / Product State Map into `01_assets/`.
3. Slot-by-slot mode: run `make-prompt-task` for one slot.
4. Batch mode: run `make-all-prompt-tasks`, generate all slots, then `set-generated-dir`.
5. Use `collect` to create a delivery manifest for human judgment.
6. Optional: run `make-all-review-tasks` to prepare strict review packets.
"""


def asset_extraction_task(state: dict[str, Any]) -> str:
    return f"""# Task For Prompt Agent: Build Product Assets

Use system prompt:
`{state['prompt_agent']}`

Platform: `{state['platform']}`

Source photos:
{source_list_markdown(state['sources'])}

Please output only the structured preparation assets first:

1. Uploaded Image Classification
2. Product Fact Assets
3. Product State Map
4. Allowed Generation States
5. Product Identity Preservation Brief
6. Product Geometry Brief
7. Geometry Anchors
8. SKU Consistency Brief, if multiple colors exist
9. Scene Options

Do not write final image prompts yet.
"""


def cmd_status(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    state = load_state(run_dir)
    print(f"Run: {run_dir.name}")
    print(f"Platform: {state['platform']}")
    for slot in state["slots"]:
        print(f"{slot['id']:10s} {slot['status']:16s} {slot['title']}")


def cmd_make_prompt_task(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    with state_transaction(run_dir) as state:
        slot = find_slot(state, args.slot)
        directory = slot_dir(run_dir, slot["id"])
        write_text(directory / "prompt_task.md", prompt_task_text(state, run_dir, slot))
        slot["status"] = "prompt_task_ready"
    print(f"Wrote: {directory / 'prompt_task.md'}")


def cmd_make_source_classification_task(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    state = load_state(run_dir)
    out = run_dir / "01_prompt_agent" / "source_classification_task.md"
    write_text(out, source_classification_task_text(state))
    print(f"Wrote: {out}")


def cmd_set_source_classification(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    source = Path(args.file).expanduser()
    out = run_dir / "01_assets" / "source_classification.md"
    write_text(out, source.read_text(encoding="utf-8"))
    print(f"Saved source classification: {out}")


def cmd_make_master_plan_task(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    state = load_state(run_dir)
    out = masters_dir(run_dir) / "master_plan_task.md"
    write_text(out, master_plan_task_text(state, run_dir))
    print(f"Wrote: {out}")


def cmd_set_master_plan(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    source = Path(args.file).expanduser()
    data = json.loads(source.read_text(encoding="utf-8"))
    out = masters_dir(run_dir) / "master_plan.json"
    write_json(out, data)
    load_master_plan(run_dir)
    print(f"Saved master plan: {out}")


def cmd_make_master_tasks(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    count = create_master_tasks(run_dir, load_state(run_dir))
    print(f"Wrote {count} master tasks under: {masters_dir(run_dir)}")


def cmd_set_master_prompt(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    master = find_master(run_dir, args.master)
    directory = master_dir(run_dir, master["id"])
    content = Path(args.file).expanduser().read_text(encoding="utf-8")
    write_text(directory / "prompt.md", content)
    write_json(
        directory / "master_state.json",
        {
            "id": master["id"],
            "status": "ready_to_generate",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    print(f"Saved master prompt: {directory / 'prompt.md'}")


def cmd_set_master(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    master = find_master(run_dir, args.master)
    directory = master_dir(run_dir, master["id"])
    image = Path(args.image).expanduser()
    write_json(
        directory / "generated.json",
        {"generated_image": str(image), "recorded_at": datetime.now().isoformat(timespec="seconds")},
    )
    write_json(
        directory / "master_state.json",
        {
            "id": master["id"],
            "status": "needs_review",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    print(f"Recorded generated master for {master['id']}: {image}")


def cmd_triage_master(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    status = MASTER_DECISIONS[args.decision]
    master = find_master(run_dir, args.master)
    directory = master_dir(run_dir, master["id"])
    write_json(
        directory / "master_state.json",
        {
            "id": master["id"],
            "status": status,
            "human_decision": args.decision,
            "human_note": args.note or "",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    write_text(
        directory / "human_triage.md",
        f"# Human Triage: {master['id']}\n\nDecision: {args.decision}\nStatus: {status}\nNote: {args.note or ''}\n",
    )
    print(f"Marked master {master['id']}: {status}")


def cmd_make_master_review_task(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    state = load_state(run_dir)
    master = find_master(run_dir, args.master)
    directory = master_dir(run_dir, master["id"])
    prompt_path = directory / "prompt.md"
    generated_path = directory / "generated.json"
    if not prompt_path.exists():
        raise SystemExit(f"Missing master prompt: {prompt_path}")
    if not generated_path.exists():
        raise SystemExit(f"Missing generated master image record: {generated_path}")
    generated = read_json(generated_path)["generated_image"]
    out = directory / "review_task.md"
    write_text(out, master_review_task_text(state, run_dir, master, generated, prompt_path))
    write_json(
        directory / "master_state.json",
        {
            "id": master["id"],
            "status": "review_task_ready",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    print(f"Wrote: {out}")


def cmd_set_master_review(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    master = find_master(run_dir, args.master)
    directory = master_dir(run_dir, master["id"])
    content = Path(args.file).expanduser().read_text(encoding="utf-8")
    write_text(directory / "review.md", content)
    decision = parse_decision(content)
    if decision == "PASS":
        status = "passed"
    elif decision in {"REVISE", "FAIL"}:
        status = "needs_revision"
    else:
        status = "review_recorded_unknown"
    write_json(
        directory / "master_state.json",
        {
            "id": master["id"],
            "status": status,
            "review_decision": decision,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    print(f"Saved master review for {master['id']}: {decision}")


def cmd_make_master_revision_task(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    state = load_state(run_dir)
    master = find_master(run_dir, args.master)
    directory = master_dir(run_dir, master["id"])
    prompt_path = directory / "prompt.md"
    review_path = directory / "review.md"
    if not prompt_path.exists():
        raise SystemExit(f"Missing original master prompt: {prompt_path}")
    review_text = review_path.read_text(encoding="utf-8") if review_path.exists() else "(No review file; use human note/status.)"
    task = f"""# Task For Prompt Agent: Revise Product Master Prompt

Use system prompt:
`{state['prompt_agent']}`

Platform: `{state['platform']}`
Master: `{master['id']}` - {master.get('title', '')}
Purpose: {master.get('purpose', '')}
SKU: {master.get('sku', '')}
Product state: {master.get('state', '')}
Angle: {master.get('angle', '')}

Original master prompt:
`{prompt_path}`

Review / human feedback:
```markdown
{review_text}
```

Shared assets:
- Source Classification: `{run_dir / '01_assets' / 'source_classification.md'}`
- Product Fact Assets: `{run_dir / '01_assets' / 'product_fact_assets.md'}`
- Geometry Anchors: `{run_dir / '01_assets' / 'geometry_anchors.md'}`
- Product State Map: `{run_dir / '01_assets' / 'product_state_map.md'}`
- SKU Consistency Brief: `{run_dir / '01_assets' / 'sku_consistency_brief.md'}`

Instructions:
- Return a revised image generation prompt for this master only.
- Preserve parts of the original prompt that worked.
- Apply the Corrective Prompt Delta or human feedback.
- Keep this master tied to its primary source photos and do not broaden back to all source photos.
"""
    out = directory / "revision_task.md"
    write_text(out, task)
    print(f"Wrote: {out}")


def cmd_make_slot_control_packet(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    out = create_slot_control_packet(run_dir, load_state(run_dir), args.slot)
    print(f"Wrote: {out}")


def cmd_run_agent(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    task_path = Path(args.task).expanduser()
    if not task_path.is_absolute():
        task_path = run_dir / task_path
    output_path = Path(args.out).expanduser() if args.out else default_agent_output_path(task_path)
    if not output_path.is_absolute():
        output_path = run_dir / output_path
    command = run_local_agent(
        state=load_state(run_dir),
        role=args.role,
        task_path=task_path,
        output_path=output_path,
        backend=args.backend,
        include_images=not args.no_images,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        print(" ".join(command))
    else:
        print(f"Wrote agent output: {output_path}")


def cmd_make_all_prompt_tasks(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    count = 0
    with state_transaction(run_dir) as state:
        for slot in state["slots"]:
            if args.only_missing and (slot_dir(run_dir, slot["id"]) / "prompt.md").exists():
                continue
            directory = slot_dir(run_dir, slot["id"])
            write_text(directory / "prompt_task.md", prompt_task_text(state, run_dir, slot))
            if slot["status"] == "needs_prompt":
                slot["status"] = "prompt_task_ready"
            count += 1
    print(f"Wrote {count} prompt tasks under: {run_dir / '02_slots'}")


def cmd_set_prompt(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    with state_transaction(run_dir) as state:
        slot = find_slot(state, args.slot)
        slot_dir = run_dir / "02_slots" / slot["id"]
        content = Path(args.file).read_text(encoding="utf-8")
        write_text(slot_dir / "prompt.md", content)
        slot["status"] = "ready_to_generate"
    print(f"Saved prompt: {slot_dir / 'prompt.md'}")


def cmd_set_prompts_dir(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    input_dir = Path(args.dir).expanduser()
    count = 0
    missing = []
    with state_transaction(run_dir) as state:
        for slot in state["slots"]:
            source = find_named_file(input_dir, slot["id"], PROMPT_EXTENSIONS)
            if not source:
                missing.append(slot["id"])
                continue
            directory = slot_dir(run_dir, slot["id"])
            write_text(directory / "prompt.md", source.read_text(encoding="utf-8"))
            slot["status"] = "ready_to_generate"
            count += 1
    print(f"Imported {count} prompts from: {input_dir}")
    if missing:
        print("Missing prompt files for: " + ", ".join(missing))


def cmd_set_generated(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    with state_transaction(run_dir) as state:
        slot = find_slot(state, args.slot)
        slot_dir = run_dir / "02_slots" / slot["id"]
        image = Path(args.image).expanduser()
        record = {"generated_image": str(image), "recorded_at": datetime.now().isoformat(timespec="seconds")}
        write_json(slot_dir / "generated.json", record)
        slot["status"] = "needs_review"
    print(f"Recorded generated image for {slot['id']}: {image}")


def cmd_set_generated_dir(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    image_dir = Path(args.dir).expanduser()
    count = 0
    missing = []
    with state_transaction(run_dir) as state:
        for slot in state["slots"]:
            image = find_named_file(image_dir, slot["id"], IMAGE_EXTENSIONS)
            if not image:
                missing.append(slot["id"])
                continue
            directory = slot_dir(run_dir, slot["id"])
            record = {"generated_image": str(image), "recorded_at": datetime.now().isoformat(timespec="seconds")}
            write_json(directory / "generated.json", record)
            slot["status"] = "needs_review"
            count += 1
    print(f"Recorded {count} generated images from: {image_dir}")
    if missing:
        print("Missing image files for: " + ", ".join(missing))


def cmd_make_review_task(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    with state_transaction(run_dir) as state:
        slot = find_slot(state, args.slot)
        slot_dir = run_dir / "02_slots" / slot["id"]
        prompt_path = slot_dir / "prompt.md"
        generated_path = slot_dir / "generated.json"
        if not prompt_path.exists():
            raise SystemExit(f"Missing prompt: {prompt_path}")
        if not generated_path.exists():
            raise SystemExit(f"Missing generated image record: {generated_path}")
        generated = read_json(generated_path)["generated_image"]
        write_text(slot_dir / "review_task.md", review_task_text(state, run_dir, slot, generated, prompt_path))
        slot["status"] = "review_task_ready"
    print(f"Wrote: {slot_dir / 'review_task.md'}")


def cmd_make_all_review_tasks(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    count = 0
    skipped = []
    with state_transaction(run_dir) as state:
        for slot in state["slots"]:
            directory = slot_dir(run_dir, slot["id"])
            prompt_path = directory / "prompt.md"
            generated_path = directory / "generated.json"
            if not prompt_path.exists() or not generated_path.exists():
                skipped.append(slot["id"])
                continue
            generated = read_json(generated_path)["generated_image"]
            write_text(directory / "review_task.md", review_task_text(state, run_dir, slot, generated, prompt_path))
            slot["status"] = "review_task_ready"
            count += 1
    print(f"Wrote {count} review tasks under: {run_dir / '02_slots'}")
    if skipped:
        print("Skipped slots missing prompt or generated image: " + ", ".join(skipped))


def parse_decision(text: str) -> str:
    match = re.search(r"\b(PASS|REVISE|FAIL)\b", text, flags=re.IGNORECASE)
    return match.group(1).upper() if match else "UNKNOWN"


def cmd_set_review(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    with state_transaction(run_dir) as state:
        slot = find_slot(state, args.slot)
        slot_dir = run_dir / "02_slots" / slot["id"]
        content = Path(args.file).read_text(encoding="utf-8")
        write_text(slot_dir / "review.md", content)
        decision = parse_decision(content)
        slot["review_decision"] = decision
        if decision == "PASS":
            slot["status"] = "passed"
        elif decision in {"REVISE", "FAIL"}:
            slot["status"] = "needs_revision"
        else:
            slot["status"] = "review_recorded_unknown"
    print(f"Saved review for {slot['id']}: {decision}")


def cmd_triage(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    status = HUMAN_DECISIONS[args.decision]
    with state_transaction(run_dir) as state:
        slot = find_slot(state, args.slot)
        slot["status"] = status
        slot["human_decision"] = args.decision
        slot["human_note"] = args.note or ""
        slot["human_decided_at"] = datetime.now().isoformat(timespec="seconds")
        notes_path = slot_dir(run_dir, slot["id"]) / "human_triage.md"
        write_text(
            notes_path,
            f"# Human Triage: {slot['id']}\n\nDecision: {args.decision}\nStatus: {status}\nNote: {args.note or ''}\n",
        )
    print(f"Marked {args.slot}: {status}")


def cmd_triage_file(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    triage = read_json(Path(args.file))
    updated = 0
    with state_transaction(run_dir) as state:
        for item in triage.get("slots", []):
            slot_id = item["slot"]
            decision = item["decision"]
            if decision not in HUMAN_DECISIONS:
                raise SystemExit(f"Invalid decision for {slot_id}: {decision}")
            slot = find_slot(state, slot_id)
            slot["status"] = HUMAN_DECISIONS[decision]
            slot["human_decision"] = decision
            slot["human_note"] = item.get("note", "")
            slot["human_decided_at"] = datetime.now().isoformat(timespec="seconds")
            notes_path = slot_dir(run_dir, slot_id) / "human_triage.md"
            write_text(
                notes_path,
                f"# Human Triage: {slot_id}\n\nDecision: {decision}\nStatus: {HUMAN_DECISIONS[decision]}\nNote: {item.get('note', '')}\n",
            )
            updated += 1
    print(f"Updated {updated} slots from triage file.")


def cmd_make_review_tasks_for_triage(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    target_statuses = set(args.status)
    count = 0
    skipped = []
    with state_transaction(run_dir) as state:
        for slot in state["slots"]:
            if slot.get("status") not in target_statuses:
                continue
            directory = slot_dir(run_dir, slot["id"])
            prompt_path = directory / "prompt.md"
            generated_path = directory / "generated.json"
            if not prompt_path.exists() or not generated_path.exists():
                skipped.append(slot["id"])
                continue
            generated = read_json(generated_path)["generated_image"]
            write_text(directory / "review_task.md", review_task_text(state, run_dir, slot, generated, prompt_path))
            slot["status"] = "review_task_ready"
            count += 1
    print(f"Wrote {count} triage-selected review tasks.")
    if skipped:
        print("Skipped slots missing prompt or generated image: " + ", ".join(skipped))


def cmd_make_revision_task(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    state = load_state(run_dir)
    slot = find_slot(state, args.slot)
    directory = slot_dir(run_dir, slot["id"])
    review_path = directory / "review.md"
    prompt_path = directory / "prompt.md"
    if not prompt_path.exists():
        raise SystemExit(f"Missing original prompt: {prompt_path}")
    review_text = review_path.read_text(encoding="utf-8") if review_path.exists() else "(No review file; use human note/status.)"
    task = f"""# Task For Prompt Agent: Revise Failed Slot Prompt

Use system prompt:
`{state['prompt_agent']}`

Platform: `{state['platform']}`
Slot: `{slot['id']}` - {slot['title']}
Current status: `{slot.get('status')}`
Human note: {slot.get('human_note', '')}

Source photos:
{source_list_markdown(state['sources'])}

Original prompt:
`{prompt_path}`

Review / human feedback:
```markdown
{review_text}
```

Shared assets:
- Product Fact Assets: `{run_dir / '01_assets' / 'product_fact_assets.md'}`
- Geometry Anchors: `{run_dir / '01_assets' / 'geometry_anchors.md'}`
- Product State Map: `{run_dir / '01_assets' / 'product_state_map.md'}`
- SKU Consistency Brief: `{run_dir / '01_assets' / 'sku_consistency_brief.md'}`

Instructions:
- Return a revised prompt for this slot only.
- Preserve any parts of the original prompt that worked.
- Apply the Corrective Prompt Delta or human feedback.
- If review says DIRECT_REGENERATE, only add small negative-prompt or emphasis changes.
- If review says REVISE_PROMPT, rewrite the missing constraints clearly.
"""
    write_text(directory / "revision_task.md", task)
    print(f"Wrote: {directory / 'revision_task.md'}")


def cmd_next(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    state = load_state(run_dir)
    for slot in state["slots"]:
        if slot["status"] != "passed":
            print(f"Next slot: {slot['id']} ({slot['status']}) - {slot['title']}")
            return
    print("All slots passed.")


def cmd_collect(args: argparse.Namespace) -> None:
    run_dir = run_path(args.run)
    state = load_state(run_dir)
    lines = [
        f"# Delivery Manifest: {state['name']}",
        "",
        f"Platform: `{state['platform']}`",
        f"Run: `{run_dir.name}`",
        "",
        "## Generated Images",
        "",
        "| Slot | Status | Generated Image | Review |",
        "| --- | --- | --- | --- |",
    ]
    for slot in state["slots"]:
        directory = slot_dir(run_dir, slot["id"])
        generated_path = directory / "generated.json"
        review_path = directory / "review.md"
        image = ""
        if generated_path.exists():
            image = read_json(generated_path).get("generated_image", "")
        review = str(review_path) if review_path.exists() else ""
        lines.append(f"| {slot['id']} | {slot['status']} | `{image}` | `{review}` |")
    lines.extend(
        [
            "",
        "## Human Review Notes",
        "",
        "Use either per-slot commands:",
        "",
        "```bash",
        f"python3 orchestrator.py triage --run {run_dir.name} --slot main_1 --decision accept --note \"usable\"",
        f"python3 orchestrator.py triage --run {run_dir.name} --slot main_2 --decision review --note \"lid looks off\"",
        "```",
        "",
        "Or create `human_triage.json` using this format:",
        "",
        "```json",
        "{",
        "  \"slots\": [",
        "    {\"slot\": \"main_1\", \"decision\": \"accept\", \"note\": \"usable\"},",
        "    {\"slot\": \"main_2\", \"decision\": \"review\", \"note\": \"handle shape off\"}",
        "  ]",
        "}",
        "```",
        "",
        "Decisions: `accept`, `review`, `regenerate`, `revise-prompt`, `reject`.",
        "",
    ]
    )
    out = run_dir / "04_delivery" / "delivery_manifest.md"
    write_text(out, "\n".join(lines))
    print(f"Wrote: {out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Water bottle agent orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Create a new run")
    p.add_argument("--name", required=True)
    p.add_argument("--platform", required=True, choices=["taobao", "淘宝", "1688"])
    p.add_argument("--source", action="append", default=[], required=True)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("status", help="Show run status")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("make-prompt-task", help="Create a prompt-agent task for one slot")
    p.add_argument("--run", required=True)
    p.add_argument("--slot", required=True)
    p.set_defaults(func=cmd_make_prompt_task)

    p = sub.add_parser("make-source-classification-task", help="Create a prompt-agent task to classify uploaded source images")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_make_source_classification_task)

    p = sub.add_parser("set-source-classification", help="Save source classification markdown under 01_assets")
    p.add_argument("--run", required=True)
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_set_source_classification)

    p = sub.add_parser("make-master-plan-task", help="Create a prompt-agent task to convert source classification into a JSON master plan")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_make_master_plan_task)

    p = sub.add_parser("set-master-plan", help="Save product master plan JSON under 01_masters")
    p.add_argument("--run", required=True)
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_set_master_plan)

    p = sub.add_parser("make-master-tasks", help="Create one master prompt task per product master in master_plan.json")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_make_master_tasks)

    p = sub.add_parser("set-master-prompt", help="Record generated prompt for one product master")
    p.add_argument("--run", required=True)
    p.add_argument("--master", required=True)
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_set_master_prompt)

    p = sub.add_parser("set-master", help="Record generated image for one product master")
    p.add_argument("--run", required=True)
    p.add_argument("--master", required=True)
    p.add_argument("--image", required=True)
    p.set_defaults(func=cmd_set_master)

    p = sub.add_parser("triage-master", help="Record human triage for one product master")
    p.add_argument("--run", required=True)
    p.add_argument("--master", required=True)
    p.add_argument("--decision", required=True, choices=sorted(MASTER_DECISIONS))
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_triage_master)

    p = sub.add_parser("make-master-review-task", help="Create a review-agent task for one product master")
    p.add_argument("--run", required=True)
    p.add_argument("--master", required=True)
    p.set_defaults(func=cmd_make_master_review_task)

    p = sub.add_parser("set-master-review", help="Record review-agent result for one product master")
    p.add_argument("--run", required=True)
    p.add_argument("--master", required=True)
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_set_master_review)

    p = sub.add_parser("make-master-revision-task", help="Create a prompt-agent revision task for one product master")
    p.add_argument("--run", required=True)
    p.add_argument("--master", required=True)
    p.set_defaults(func=cmd_make_master_revision_task)

    p = sub.add_parser("make-slot-control-packet", help="Create a slot generation packet from accepted product masters")
    p.add_argument("--run", required=True)
    p.add_argument("--slot", required=True)
    p.set_defaults(func=cmd_make_slot_control_packet)

    p = sub.add_parser("run-agent", help="Run the local prompt or review agent against a task file")
    p.add_argument("--run", required=True)
    p.add_argument("--role", required=True, choices=["prompt", "review"])
    p.add_argument("--task", required=True, help="Task path, absolute or relative to the run directory")
    p.add_argument("--out", help="Output path, absolute or relative to the run directory")
    p.add_argument("--backend", default="codex", choices=["codex", "hermes"])
    p.add_argument("--no-images", action="store_true", help="Do not attach image files to the local agent call")
    p.add_argument("--dry-run", action="store_true", help="Print the local agent command without executing it")
    p.set_defaults(func=cmd_run_agent)

    p = sub.add_parser("make-all-prompt-tasks", help="Create prompt-agent tasks for all slots")
    p.add_argument("--run", required=True)
    p.add_argument("--only-missing", action="store_true")
    p.set_defaults(func=cmd_make_all_prompt_tasks)

    p = sub.add_parser("set-prompt", help="Record generated slot prompt")
    p.add_argument("--run", required=True)
    p.add_argument("--slot", required=True)
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_set_prompt)

    p = sub.add_parser("set-prompts-dir", help="Import prompts named <slot>.md or <slot>.txt from a directory")
    p.add_argument("--run", required=True)
    p.add_argument("--dir", required=True)
    p.set_defaults(func=cmd_set_prompts_dir)

    p = sub.add_parser("set-generated", help="Record generated image path")
    p.add_argument("--run", required=True)
    p.add_argument("--slot", required=True)
    p.add_argument("--image", required=True)
    p.set_defaults(func=cmd_set_generated)

    p = sub.add_parser("set-generated-dir", help="Import generated images named <slot>.<ext> from a directory")
    p.add_argument("--run", required=True)
    p.add_argument("--dir", required=True)
    p.set_defaults(func=cmd_set_generated_dir)

    p = sub.add_parser("make-review-task", help="Create a review-agent task for one slot")
    p.add_argument("--run", required=True)
    p.add_argument("--slot", required=True)
    p.set_defaults(func=cmd_make_review_task)

    p = sub.add_parser("make-all-review-tasks", help="Create review-agent tasks for all slots with prompts and images")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_make_all_review_tasks)

    p = sub.add_parser("set-review", help="Record review-agent result")
    p.add_argument("--run", required=True)
    p.add_argument("--slot", required=True)
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_set_review)

    p = sub.add_parser("triage", help="Record human triage for one slot")
    p.add_argument("--run", required=True)
    p.add_argument("--slot", required=True)
    p.add_argument("--decision", required=True, choices=sorted(HUMAN_DECISIONS))
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_triage)

    p = sub.add_parser("triage-file", help="Record human triage from a JSON file")
    p.add_argument("--run", required=True)
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_triage_file)

    p = sub.add_parser("make-review-tasks-for-triage", help="Create review tasks only for selected triage statuses")
    p.add_argument("--run", required=True)
    p.add_argument(
        "--status",
        action="append",
        default=["needs_review_agent", "needs_regeneration", "needs_prompt_revision"],
        help="Slot status to include. Can be repeated.",
    )
    p.set_defaults(func=cmd_make_review_tasks_for_triage)

    p = sub.add_parser("make-revision-task", help="Create a prompt-agent revision task for one slot")
    p.add_argument("--run", required=True)
    p.add_argument("--slot", required=True)
    p.set_defaults(func=cmd_make_revision_task)

    p = sub.add_parser("next", help="Show next unfinished slot")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("collect", help="Create a delivery manifest for all generated images")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_collect)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
