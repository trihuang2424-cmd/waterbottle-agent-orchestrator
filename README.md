# Water Bottle Agent Orchestrator

This is a local automation layer for chaining:

```text
prompt-agent -> image generation -> review-agent -> pass/revise/fail loop
```

It is file-based for the MVP. The default workflow is now batch-first: prepare all slots, generate all images, collect the full set, then judge manually or run review-agent tasks.

## Create A Run

```bash
cd /Users/andrea/jacky/waterbottle-agent-orchestrator
python3 orchestrator.py init \
  --name campus-cup-test \
  --platform taobao \
  --source "/Users/andrea/Pictures/照片图库.photoslibrary/originals/C/CC534849-B7A1-497E-9A26-A451F28D00C5.jpeg" \
  --source "/Users/andrea/Pictures/照片图库.photoslibrary/originals/C/CC3E7345-8BFC-4051-9745-463EADBC03C0.jpeg"
```

The command creates `runs/<run-id>/`.

## Master-First Mode

Use this when source photos contain multiple product states, angles, or SKU colors and you want faster, steadier generation.

### Step 1A: Classify Source Photos

```bash
python3 orchestrator.py make-source-classification-task --run <run-id>
```

Send this task to `waterbottle-prompt-agent`, then save the returned markdown:

```bash
python3 orchestrator.py set-source-classification --run <run-id> --file /path/source_classification.md
```

The classification is automatic and does not require human approval, but it is stored at:

```text
runs/<run-id>/01_assets/source_classification.md
```

### Step 1B: Build A Master Plan

```bash
python3 orchestrator.py make-master-plan-task --run <run-id>
python3 orchestrator.py set-master-plan --run <run-id> --file /path/master_plan.json
```

The plan defines a flexible set of product masters based on the uploaded photos, such as closed-front, open-lid, folded-handle, side-scale, or SKU-lineup masters. Masters are not fixed templates.

### Step 1C: Generate And Confirm Masters

```bash
python3 orchestrator.py make-master-tasks --run <run-id>
python3 orchestrator.py set-master-prompt --run <run-id> --master front_closed_blue --file /path/front_closed_blue.md
python3 orchestrator.py set-master --run <run-id> --master front_closed_blue --image /path/front_closed_blue.png
python3 orchestrator.py triage-master --run <run-id> --master front_closed_blue --decision accept --note "geometry usable"
```

If a master is uncertain or bad:

```bash
python3 orchestrator.py make-master-review-task --run <run-id> --master open_lid_pink
python3 orchestrator.py set-master-review --run <run-id> --master open_lid_pink --file /path/review.md
python3 orchestrator.py make-master-revision-task --run <run-id> --master open_lid_pink
```

Only accepted or passed masters should be used for final slot generation.

### Step 1D: Create Slot Control Packets From Masters

```bash
python3 orchestrator.py make-slot-control-packet --run <run-id> --slot main_2
```

This creates:

```text
runs/<run-id>/02_slots/<slot>/slot_control_packet.md
```

The packet binds a slot to accepted masters and explicitly tells the generation step not to attach all source photos.

## Step 1: Build Shared Assets

Open:

```text
runs/<run-id>/01_prompt_agent/asset_extraction_task.md
```

Send that task to `waterbottle-prompt-agent`, then paste the returned sections into:

```text
runs/<run-id>/01_assets/product_fact_assets.md
runs/<run-id>/01_assets/geometry_anchors.md
runs/<run-id>/01_assets/product_state_map.md
runs/<run-id>/01_assets/sku_consistency_brief.md
```

## Batch Mode

Use this when you want to generate the whole set first and judge afterward.

### Step 2: Create Prompt Tasks For All Slots

```bash
python3 orchestrator.py make-all-prompt-tasks --run <run-id>
```

This creates one task per slot:

```text
runs/<run-id>/02_slots/<slot>/prompt_task.md
```

Send each task to `waterbottle-prompt-agent`. Save returned prompts into one folder using slot filenames:

```text
main_1.md
main_2.md
main_3.md
main_4.md
main_5.md
detail_1.md
...
```

Import all prompts:

```bash
python3 orchestrator.py set-prompts-dir --run <run-id> --dir /path/to/prompts
```

### Step 3: Generate All Images

Use your image model to generate every slot. Save files using slot filenames:

```text
main_1.png
main_2.png
main_3.png
main_4.png
main_5.png
detail_1.png
...
```

Import all generated images:

```bash
python3 orchestrator.py set-generated-dir --run <run-id> --dir /path/to/generated-images
```

### Step 4: Collect For Human Judgment

```bash
python3 orchestrator.py collect --run <run-id>
```

Open:

```text
runs/<run-id>/04_delivery/delivery_manifest.md
```

This manifest lists all generated image paths and statuses for a full-set human review.

### Step 5: Human Triage First

After opening `delivery_manifest.md`, mark each slot:

- `accept`: usable, keep directly.
- `review`: uncertain, send to review-agent for scoring and diagnosis.
- `regenerate`: prompt seems okay, image result is bad; likely regenerate directly.
- `revise-prompt`: prompt is missing constraints; ask prompt-agent to revise.
- `reject`: do not use.

Per-slot example:

```bash
python3 orchestrator.py triage --run <run-id> --slot main_1 --decision accept --note "usable"
python3 orchestrator.py triage --run <run-id> --slot main_2 --decision review --note "lid shape may have drifted"
python3 orchestrator.py triage --run <run-id> --slot detail_3 --decision revise-prompt --note "missing geometry anchors"
```

Or create a JSON file:

```json
{
  "slots": [
    {"slot": "main_1", "decision": "accept", "note": "usable"},
    {"slot": "main_2", "decision": "review", "note": "lid shape may have drifted"},
    {"slot": "detail_3", "decision": "revise-prompt", "note": "missing geometry anchors"}
  ]
}
```

Then import it:

```bash
python3 orchestrator.py triage-file --run <run-id> --file /path/human_triage.json
```

### Step 6: Review Only Problem Slots

```bash
python3 orchestrator.py make-review-tasks-for-triage --run <run-id>
```

This only creates review tasks for slots marked:

- `needs_review_agent`
- `needs_regeneration`
- `needs_prompt_revision`

Send those review tasks to `waterbottle-review-agent`. The review-agent should decide:

- `DIRECT_REGENERATE`: regenerate using the same prompt or tiny delta.
- `REVISE_PROMPT`: revise prompt before regeneration.
- `REQUEST_MORE_SOURCE`: source photos/assets are insufficient.

### Step 7: Revise Selected Prompts

For a slot that needs prompt revision:

```bash
python3 orchestrator.py make-revision-task --run <run-id> --slot main_2
```

Send `revision_task.md` to `waterbottle-prompt-agent`, save the revised prompt, regenerate that image, and rerun collect or review as needed.

### Optional: Prepare Review-Agent Tasks For All Slots

```bash
python3 orchestrator.py make-all-review-tasks --run <run-id>
```

This creates review packets for the full set. Use it only when you want full strict review.

## Slot-By-Slot Mode

Use this when quality is more important than speed.

```bash
python3 orchestrator.py make-prompt-task --run <run-id> --slot main_1
python3 orchestrator.py set-prompt --run <run-id> --slot main_1 --file /path/to/main_1_prompt.md
python3 orchestrator.py set-generated --run <run-id> --slot main_1 --image /path/to/main_1_generated.png
python3 orchestrator.py make-review-task --run <run-id> --slot main_1
python3 orchestrator.py set-review --run <run-id> --slot main_1 --file /path/to/main_1_review.md
```

Then check:

```bash
python3 orchestrator.py status --run <run-id>
python3 orchestrator.py next --run <run-id>
```

## Slots

Taobao runs create:

- `main_1` to `main_5`
- `detail_1` to `detail_8`

1688 runs create:

- `main_1` to `main_5`
- `detail_1` to `detail_10`

## Batch Commands

```bash
python3 orchestrator.py make-source-classification-task --run <run-id>
python3 orchestrator.py set-source-classification --run <run-id> --file /path/source_classification.md
python3 orchestrator.py make-master-plan-task --run <run-id>
python3 orchestrator.py set-master-plan --run <run-id> --file /path/master_plan.json
python3 orchestrator.py make-master-tasks --run <run-id>
python3 orchestrator.py set-master-prompt --run <run-id> --master front_closed_blue --file /path/master_prompt.md
python3 orchestrator.py set-master --run <run-id> --master front_closed_blue --image /path/master.png
python3 orchestrator.py triage-master --run <run-id> --master front_closed_blue --decision accept --note "usable"
python3 orchestrator.py make-master-review-task --run <run-id> --master front_closed_blue
python3 orchestrator.py set-master-review --run <run-id> --master front_closed_blue --file /path/master_review.md
python3 orchestrator.py make-master-revision-task --run <run-id> --master front_closed_blue
python3 orchestrator.py make-slot-control-packet --run <run-id> --slot main_2
python3 orchestrator.py make-all-prompt-tasks --run <run-id>
python3 orchestrator.py set-prompts-dir --run <run-id> --dir /path/to/prompts
python3 orchestrator.py set-generated-dir --run <run-id> --dir /path/to/generated-images
python3 orchestrator.py collect --run <run-id>
python3 orchestrator.py make-all-review-tasks --run <run-id>
python3 orchestrator.py triage --run <run-id> --slot main_1 --decision accept --note "usable"
python3 orchestrator.py triage-file --run <run-id> --file /path/human_triage.json
python3 orchestrator.py make-review-tasks-for-triage --run <run-id>
python3 orchestrator.py make-revision-task --run <run-id> --slot main_2
```
