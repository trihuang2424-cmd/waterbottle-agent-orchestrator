# Water Bottle Agent Orchestrator

## Role

This folder orchestrates the water bottle prompt agent and review agent through a local file-based workflow.

The orchestrator does not replace either agent:

- `waterbottle-prompt-agent` creates product facts and slot prompts.
- Image generation creates one image per slot.
- `waterbottle-review-agent` reviews the generated image against source photos and prompt assets.
- This orchestrator stores state and prepares task packets between those steps.

## Workflow Rules

- Default batch mode: prepare all slot prompts, generate all slot images, collect all outputs, then let the user judge the full set.
- Master-first mode: for complex products with multiple uploaded states/angles/SKUs, first classify source photos automatically, build a flexible Product Master Set, let humans confirm generated masters, then generate slots from accepted/passed masters.
- Master sets are not fixed templates; derive them from source classification and product coverage. Examples include angle masters, state masters, SKU masters, and mechanism/detail masters.
- Source classification does not require human approval by default, but must be saved under `01_assets/source_classification.md` for traceability.
- Final slot generation should bind each slot to at least one accepted/passed primary master when master-first mode is used; do not attach all source photos to every slot generation call.
- Preferred production loop: prompt-agent generates the full set, human triage keeps usable images, and only uncertain/bad images go to review-agent.
- Quality-gate mode: work slot by slot when the user wants strict review before continuing.
- Even in batch mode, generate each main image with a separate image-generation call.
- In batch mode, do not block later slots on review results from earlier slots.
- For accepted human-triage slots, do not run review-agent unless the user asks.
- For uncertain/bad slots, review-agent decides whether to direct-regenerate, revise prompt, or request more source photos.
- For `REVISE` or `FAIL`, feed the review agent's Corrective Prompt Delta back into the prompt agent and regenerate the same slot.
- Keep Product Fact Assets, Geometry Anchors, Product State Map, and SKU Consistency Brief under `01_assets/` for each run.

## CLI

Use `orchestrator.py`:

```bash
python3 orchestrator.py init --name test-cup --platform taobao --source /path/a.jpg --source /path/b.jpg
python3 orchestrator.py status --run <run-id>
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
python3 orchestrator.py triage --run <run-id> --slot main_1 --decision accept --note "usable"
python3 orchestrator.py triage-file --run <run-id> --file /path/human_triage.json
python3 orchestrator.py make-review-tasks-for-triage --run <run-id>
python3 orchestrator.py make-revision-task --run <run-id> --slot main_2
python3 orchestrator.py make-all-review-tasks --run <run-id>
python3 orchestrator.py make-prompt-task --run <run-id> --slot main_1
python3 orchestrator.py set-prompt --run <run-id> --slot main_1 --file /path/prompt.md
python3 orchestrator.py set-generated --run <run-id> --slot main_1 --image /path/generated.png
python3 orchestrator.py make-review-task --run <run-id> --slot main_1
python3 orchestrator.py set-review --run <run-id> --slot main_1 --file /path/review.md
python3 orchestrator.py next --run <run-id>
```
