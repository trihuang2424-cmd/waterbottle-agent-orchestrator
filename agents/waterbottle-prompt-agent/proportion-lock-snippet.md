# Proportion Lock Snippet

Use this snippet in every water bottle image prompt when source photos are provided.

## Chinese

比例锚点：将 Product Geometry Brief 中的具体比例数值或视觉估算复制到本字段，例如整体高宽比、产品占画布高度、杯身占总高比例、杯盖/提手组件占总高比例、杯盖圈与杯身宽度关系、按钮位置、吸管位置、印刷文字位置、底部凹槽位置。不要只写“保持比例”。

比例锁定：以上传产品图为唯一几何基准，保持原始高宽比、杯身粗细、杯盖大小、杯口宽度、底部宽度、肩部弧线、收腰程度、手柄/吸管/滤网/密封圈位置，以及所有部件之间的相对比例。只允许改变背景、灯光、构图、平台化文字排版和画面氛围。禁止拉长、压扁、变瘦、变胖、放大杯盖、缩小杯身、改变杯口宽度、改变底部宽度、移动手柄或吸管、把产品美化成另一种杯型。把原产品按真实比例放入目标画布，通过自然留白适配画布，不要为了填满画布而扭曲产品。

实测尺寸锁定：如果用户提供长/宽/高、杯口直径、杯身直径、底部直径、杯盖高度、手柄/吸管尺寸等数据，则以这些实测尺寸作为所有视角的最高优先级几何基准。上传图片用于参考颜色、材质、Logo、结构和细节；若图片透视与实测比例冲突，以实测尺寸为准。

## English

Geometry anchors: copy the concrete ratio values or visual estimates from the Product Geometry Brief into this field, such as overall height-to-width ratio, product canvas occupancy, body-to-total height, lid/handle assembly-to-total height, lid-band-to-body width, button position, straw position, printed text position, and bottom groove position. Do not only say "preserve proportions".

Proportion lock: use the uploaded product photo as the only geometry reference. Preserve the original height-to-width ratio, body thickness, lid size, mouth width, base width, shoulder curve, taper, handle/straw/filter/seal-ring position, and all relative part proportions. Only change the background, lighting, composition, platform-style text layout, and visual atmosphere. Do not stretch, squash, slim, widen, enlarge the lid, shrink the body, change the mouth width, change the base width, move the handle or straw, or beautify the product into a different bottle shape. Fit the original product proportion into the target canvas with natural whitespace; never distort the product to fill the canvas.

Confirmed-dimension lock: if the user provides height, width, depth, top diameter, body diameter, bottom diameter, lid height, handle/straw dimensions, or other measurements, use those dimensions as the highest-priority geometry reference across all views. Uploaded photos are references for color, material, logo, structure, and details; if photo perspective conflicts with confirmed dimensions, the confirmed dimensions win.

## Quick QA

- Is the bottle as tall/wide as the source photo?
- Is the lid still the same relative size?
- Is the body still the same thickness?
- If confirmed dimensions exist, does every view obey those dimensions rather than perspective distortion?
- Are the mouth, base, handle, straw, filter, and seal ring in the same positions?
- Did the model use whitespace to fit the canvas instead of distorting the product?
