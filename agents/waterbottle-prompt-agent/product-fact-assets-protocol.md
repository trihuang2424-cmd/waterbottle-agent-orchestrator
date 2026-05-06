# Product Fact Assets Protocol

Before generating e-commerce images, classify uploaded product photos and build a factual asset library. This prevents the image model from inventing functional details such as drinking spouts, mouthpieces, lids, handles, hinges, seal rings, and straws.

## Image Classification

Classify each uploaded image into one or more roles:

- 主体图 / hero body
- 杯盖 / lid
- 饮嘴 / drinking spout or mouthpiece
- 吸管 / straw
- 提手 / handle
- 密封结构 / seal ring, gasket, plug, locking clasp
- 杯口 / mouth opening
- 杯身 / body
- 杯底 / base
- 内胆 / liner
- Logo/印刷 / logo or print
- SKU色号 / color SKU
- 包装/配件 / packaging or accessories

## Fact Asset Table

Use this table before prompt generation:

```markdown
## Uploaded Image Classification
| Image | Role(s) | Useful Facts | Unclear Parts |
| --- | --- | --- | --- |

## Product Fact Assets
| Asset | Source Image(s) | Confirmed Facts | Uncertain / Need Confirmation | Must Preserve |
| --- | --- | --- | --- | --- |
| Overall body | ... | ... | ... | ... |
| Lid | ... | ... | ... | ... |
| Drinking spout / mouthpiece | ... | ... | ... | ... |
| Straw | ... | ... | ... | ... |
| Handle | ... | ... | ... | ... |
| Seal ring / leak-proof structure | ... | ... | ... | ... |
| Mouth opening | ... | ... | ... | ... |
| Base | ... | ... | ... | ... |
| Logo / print | ... | ... | ... | ... |
| Color SKUs | ... | ... | ... | ... |
```

## Part Locks

Use the relevant lock in every prompt that shows the part.

```text
Drinking spout lock: preserve the exact drinking spout/mouthpiece shape, opening position, angle, size relation to the lid, material, and connection to the lid from the Product Fact Assets. Do not invent a new spout, straw mouth, sip hole, nozzle, button, hinge, or cap structure.
```

```text
饮嘴锁定：严格保持事实资产库中饮嘴/饮水口的形状、开口位置、角度、与杯盖的大小关系、材质以及和杯盖的连接方式。禁止自由发挥新的吸嘴、饮水口、喷嘴、按钮、铰链或盖帽结构。
```

```text
Lid lock: preserve the exact lid silhouette, height, diameter, opening mechanism, hinge/button/lock position, cap layers, and connection to the cup body from the Product Fact Assets.
```

```text
Handle lock: preserve the exact handle position, size, curvature, attachment points, and relation to the lid/body from the Product Fact Assets.
```

```text
Seal and straw lock: preserve the visible seal ring, plug, gasket, straw path, straw angle, and straw/mouthpiece connection from the Product Fact Assets.
```

## Rule

Unknown parts are not design space. If a functional part is unclear, mark it as `待确认`, hide it naturally if possible, or ask for a close-up when that part is required.

