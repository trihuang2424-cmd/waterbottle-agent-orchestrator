# Detail Page Prompt Protocol

The agent must not stop at 5 main images. A complete first output should include multiple detail-page image prompts.

## Default Count

- Taobao: 6-8 detail-page image prompts.
- 1688: 7-10 detail-page image prompts.

## Sequence

Use buyer-decision order:

1. Product overview and core value.
2. Core selling points with confirmed facts.
3. Structure and material details.
4. Size, capacity, and scale.
5. SKU/color/capacity/lid options.
6. Usage scene.
7. Cleaning, assembly, accessories, or safety notes if relevant.
8. Packaging, customization, factory, shipping, service, or FAQ if true.

## Prompt Structure

Each detail image must include:

```markdown
### Detail Image N: ...
Purpose:
Export:
Layout:
Product source:
Proportion lock:
SKU consistency lock:
Scene relevance:
Suggested copy:
中文创意指令:
English image prompt:
Negative prompt:
Compliance check:
```

## Platform Bias

Taobao:

- consumer conversion;
- lifestyle usage;
- clean mobile-reading layout;
- restrained but emotional copy.

1688:

- procurement clarity;
- SKU and parameter completeness;
- customization, packaging, and supply capability when true;
- practical B2B trust.

