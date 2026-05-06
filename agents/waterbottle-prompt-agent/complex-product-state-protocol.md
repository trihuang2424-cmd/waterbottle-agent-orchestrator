# Complex Product State Protocol

Use this for water bottles with movable or multi-function parts: flip handles, carrying loops, flip lids, one-button lids, hidden drinking spouts, straw lids, lock buttons, removable caps, or foldable structures.

## Core Problem

Complex products often fail because AI blends multiple source states into one impossible object. For example, it may merge:

- handle folded + handle raised;
- lid closed + drinking spout exposed;
- shelf display state + carry state;
- SKU color comparison + feature demonstration.

## Required State Map

Before prompt generation, create:

```markdown
## Product State Map
| Source Image | Handle State | Lid State | Spout State | Button State | Straw State | Use This For |
| --- | --- | --- | --- | --- | --- | --- |

## Allowed Generation States
| State ID | Description | Source Image(s) | Allowed Slots | Forbidden Mixes |
| --- | --- | --- | --- | --- |
```

## State Lock

```text
State lock: use only one physical product state for this image: [state]. Do not merge handle folded and handle raised states. Do not combine lid-open, lid-closed, spout-hidden, and spout-exposed references unless the image is explicitly a labeled function diagram with separate panels. The generated product must be mechanically possible.
```

```text
状态锁定：本图只使用一个明确的真实产品状态：[状态]。禁止把提手收起和提手提起状态融合，禁止把杯盖打开/闭合、饮嘴隐藏/露出等不同状态混成一个产品，除非这是明确标注的多面板功能示意图。生成结果必须是机械结构上真实可存在的状态。
```

## Recommended Defaults

- SKU color image: same state for all colors, usually handle folded/down or not visible, lid closed.
- Carry feature image: handle raised, lid closed.
- Spout feature image: separate close-up or separate panel.
- Main hero image: one clean product state only.
- Multi-state explanation: separate panels or separate detail images.

