import tempfile
import unittest
from pathlib import Path

import orchestrator


def make_run(root: Path) -> Path:
    run_dir = root / "runs" / "run-1"
    source = root / "front.png"
    generated = root / "generated.png"
    source.write_bytes(b"source")
    generated.write_bytes(b"generated")
    state = {
        "name": "test bottle",
        "platform": "taobao",
        "created_at": "2026-05-06T00:00:00",
        "prompt_agent": str(root / "prompt-agent" / "AGENTS.md"),
        "review_agent": str(root / "review-agent" / "AGENTS.md"),
        "sources": [{"id": "source_1", "path": str(source)}],
        "slots": orchestrator.slot_plan("taobao"),
    }
    orchestrator.save_state(run_dir, state)
    (root / "prompt-agent").mkdir()
    (root / "review-agent").mkdir()
    (root / "prompt-agent" / "AGENTS.md").write_text("PROMPT AGENT", encoding="utf-8")
    (root / "review-agent" / "AGENTS.md").write_text("REVIEW AGENT", encoding="utf-8")
    return run_dir


class AgentRunnerTests(unittest.TestCase):
    def test_default_agent_paths_are_bundled_in_repository(self):
        self.assertTrue(str(orchestrator.PROMPT_AGENT).startswith(str(orchestrator.ROOT)))
        self.assertTrue(str(orchestrator.REVIEW_AGENT).startswith(str(orchestrator.ROOT)))
        self.assertEqual(orchestrator.PROMPT_AGENT.name, "AGENTS.md")
        self.assertEqual(orchestrator.REVIEW_AGENT.name, "AGENTS.md")

    def test_agent_prompt_combines_role_prompt_and_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            task = run_dir / "task.md"
            task.write_text("# Task\nDo the work.", encoding="utf-8")

            prompt = orchestrator.build_agent_prompt(orchestrator.load_state(run_dir), "prompt", task)

        self.assertIn("PROMPT AGENT", prompt)
        self.assertIn("# Task", prompt)
        self.assertIn("Do not edit files", prompt)

    def test_codex_command_attaches_images_and_writes_last_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            output = run_dir / "out.md"

            command = orchestrator.build_agent_command(
                backend="codex",
                output_path=output,
                image_paths=[Path(tmp) / "front.png"],
            )

        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--output-last-message", command)
        self.assertIn(str(output), command)
        self.assertIn("--image", command)
        self.assertIn("-", command)

    def test_review_image_paths_include_sources_and_generated_image_from_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_run(root)
            generated = root / "generated.png"
            task = run_dir / "review_task.md"
            task.write_text(f"Generated image:\n`{generated}`\n", encoding="utf-8")

            images = orchestrator.agent_image_paths(orchestrator.load_state(run_dir), "review", task)

        self.assertIn(generated, images)
        self.assertIn(root / "front.png", images)


if __name__ == "__main__":
    unittest.main()
