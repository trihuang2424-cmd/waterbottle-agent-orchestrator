# Product Identity Preservation Protocol

Use this when generated images look like a similar new bottle instead of the uploaded bottle.

## Core Rule

The uploaded product is not inspiration. It is the product.

For e-commerce images, prefer:

1. Reference-preserving edit.
2. Cutout/composite workflow.
3. Controlled SKU recolor on the same geometry master.

Avoid text-to-image reconstruction of the bottle.

## Product Identity Lock

```text
Product identity lock: do not redraw, redesign, reinterpret, beautify, or reconstruct the bottle. Use the uploaded product image/cutout as the exact product source. Preserve the exact silhouette, transparent body shape, bottom grooves, scale marks, printed text, blue lid band, orange button, transparent cap, handle arc, top grip, drinking spout, straw, seams, and all part positions. Only change the background, lighting, platform layout, and optional labels. If color variants are needed, recolor the same geometry master only; do not generate new bottle shapes.
```

```text
产品身份锁定：不要重画、重设计、重新理解、美化或重构这个水杯。以上传产品图/抠图作为唯一产品来源，严格保持原始轮廓、透明杯身形状、底部凹槽、刻度、印刷文字、蓝色杯盖圈、橙色按钮、透明上盖、提手弧度、顶部橙色握片、饮嘴、吸管、接缝和所有部件位置。只允许改变背景、灯光、平台化版式和必要标签。如果需要多色SKU，只能在同一几何母版上受控改色，禁止生成新的杯型。
```

## Drift Checklist

Reject the generated image if:

- lid ridges, textures, buttons, panels, or decorations changed;
- handle size, thickness, height, curve, or attachment changed;
- orange button shape, size, or position changed;
- transparent cap changed shape, height, width, or tint;
- body became taller, slimmer, wider, shorter, cleaner, or more symmetrical;
- molded grooves changed number, shape, or position;
- straw moved, straightened, disappeared, duplicated, or changed length;
- printed text content, font, spacing, or placement changed;
- SKU colors became different product designs rather than recolors.

