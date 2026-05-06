# Water Bottle Review Agent

This agent reviews generated e-commerce water bottle images against source product photos.

- `AGENTS.md`: review-agent system prompt.
- `review-checklist.md`: compact review checklist.

Suggested manual workflow:

1. Provide source product photo(s).
2. Provide the generated image.
3. Provide the prompt used to generate it.
4. Provide Product Fact Assets / Geometry Anchors / Product State Map if available.
5. Ask for a strict review.

Expected output: `PASS`, `REVISE`, or `FAIL`, plus exact differences and a corrective prompt delta.

