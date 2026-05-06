# Water Bottle Prompt Agent

This folder contains an MVP prompt-engineering agent for generating e-commerce water bottle image prompts for 1688 and Taobao.

- `AGENTS.md`: the system prompt / agent behavior definition.
- `platform-rules.md`: compact 1688 + Taobao rule notes for review and iteration.
- `proportion-lock-snippet.md`: reusable geometry and dimension lock text.
- `geometry-anchors-protocol.md`: requires concrete geometry ratios from the Product Geometry Brief to be copied into every final prompt.
- `scene-matrix.md`: water bottle type to scene-option matrix.
- `product-fact-assets-protocol.md`: uploaded image classification and part-level fact locks.
- `complex-product-state-protocol.md`: state locking for movable handles, flip lids, spouts, and other multi-function structures.

Suggested manual test flow:

1. Open a new conversation using the instructions in `AGENTS.md`.
2. Tell the agent the target platform: `1688` or `淘宝`.
3. Provide product photos or product facts.
4. Let the agent classify uploaded images and build Product Fact Assets.
5. If there are multiple colors, clarify whether they are the same model SKU variants.
6. Choose 1-2 scene options recommended by the agent.
7. Ask for `5张主图提示词 + 6-10张详情页图片提示词`.
8. Generate each main image with a separate call. Start with one image slot, inspect it, then iterate.
