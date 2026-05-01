import json
import tempfile
import unittest
from pathlib import Path

import orchestrator


def make_run(root: Path) -> Path:
    run_dir = root / "runs" / "run-1"
    state = {
        "name": "test bottle",
        "platform": "taobao",
        "created_at": "2026-05-02T00:00:00",
        "prompt_agent": "/tmp/prompt-agent/AGENTS.md",
        "review_agent": "/tmp/review-agent/AGENTS.md",
        "sources": [
            {"id": "source_1", "path": "/tmp/front.jpg"},
            {"id": "source_2", "path": "/tmp/lid.jpg"},
        ],
        "slots": orchestrator.slot_plan("taobao"),
    }
    orchestrator.save_state(run_dir, state)
    for name in [
        "source_classification.md",
        "product_fact_assets.md",
        "geometry_anchors.md",
        "product_state_map.md",
        "sku_consistency_brief.md",
    ]:
        orchestrator.write_text(run_dir / "01_assets" / name, f"# {name}\n")
    return run_dir


class MasterWorkflowTests(unittest.TestCase):
    def test_source_classification_task_requests_structured_classification(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            state = orchestrator.load_state(run_dir)

            text = orchestrator.source_classification_task_text(state)

        self.assertIn("Source Image Classification", text)
        self.assertIn("source_1", text)
        self.assertIn("SKU", text)
        self.assertIn("master candidates", text)

    def test_master_plan_json_creates_one_task_per_master(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            plan_path = run_dir / "01_masters" / "master_plan.json"
            orchestrator.write_json(
                plan_path,
                {
                    "masters": [
                        {
                            "id": "front_closed_blue",
                            "title": "Blue front closed",
                            "purpose": "Full product geometry master",
                            "primary_sources": ["source_1"],
                            "secondary_sources": ["source_2"],
                            "serves_slots": ["main_2", "main_5"],
                            "sku": "blue",
                            "state": "closed lid, raised handle",
                            "angle": "front",
                            "notes": "Keep slogan readable.",
                        }
                    ]
                },
            )

            count = orchestrator.create_master_tasks(run_dir, orchestrator.load_state(run_dir))

            task_path = run_dir / "01_masters" / "front_closed_blue" / "master_task.md"
            self.assertEqual(count, 1)
            self.assertTrue(task_path.exists())
            task_text = task_path.read_text(encoding="utf-8")
            self.assertIn("Blue front closed", task_text)
            self.assertIn("source_1", task_text)
            self.assertIn("main_2", task_text)

    def test_slot_control_packet_uses_accepted_master_and_avoids_all_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            orchestrator.write_json(
                run_dir / "01_masters" / "master_plan.json",
                {
                    "masters": [
                        {
                            "id": "front_closed_blue",
                            "title": "Blue front closed",
                            "purpose": "Full product geometry master",
                            "primary_sources": ["source_1"],
                            "secondary_sources": [],
                            "serves_slots": ["main_2"],
                            "sku": "blue",
                            "state": "closed lid",
                            "angle": "front",
                            "notes": "",
                        }
                    ]
                },
            )
            master_dir = run_dir / "01_masters" / "front_closed_blue"
            orchestrator.write_json(master_dir / "generated.json", {"generated_image": "/tmp/master.png"})
            orchestrator.write_json(master_dir / "master_state.json", {"status": "accepted_by_human"})

            packet_path = orchestrator.create_slot_control_packet(
                run_dir, orchestrator.load_state(run_dir), "main_2"
            )

            packet = packet_path.read_text(encoding="utf-8")
            self.assertIn("primary master", packet.lower())
            self.assertIn("/tmp/master.png", packet)
            self.assertIn("Do not attach all source photos", packet)
            self.assertNotIn("/tmp/lid.jpg", packet)


if __name__ == "__main__":
    unittest.main()
