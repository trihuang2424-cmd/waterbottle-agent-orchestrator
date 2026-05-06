# 1688 + Taobao Water Bottle Image Rule Notes

Updated: 2026-04-29

This is an MVP research note for prompt engineering tests. It is not a final compliance document. For production uploads, check the latest merchant backend rules by platform and category.

## Taobao

| Area | Working Rule | Confidence | Prompt Implication |
| --- | --- | --- | --- |
| Main image count | Up to 5 square main images | High | Build 5 fixed slots |
| Square main image | 800 x 800 px baseline; 1000 x 1000+ also useful | High | Default export `1:1, 1000 x 1000` unless user asks 800 |
| Format | JPG/JPEG/PNG | High | Avoid GIF |
| File size | Common target <= 3 MB | Medium | Mention compression after generation |
| White-background image | Treat image 5 as white-background product image | Medium-high | No text, no logo overlay, no collage |
| Optional 3:4 image | 750 x 1000 / 900 x 1200 / higher 3:4 variants | Medium | Add only when user asks for mobile feed material |
| Detail images | Width often 620-1500 px; height <= 2000 px per image; <= 3 MB; jpg/jpeg/png | Medium | Split details into modules |
| Text on main image | Avoid heavy text and promotional clutter | High | Main image 1 gets little/no text |
| Forbidden elements | Contact info, external links, QR codes, other-platform watermarks, exaggerated promo | High | Add to negative prompt |
| Product proportion | Product must keep source-photo geometry inside target canvas | High for prompt quality | Add whitespace instead of stretching or slimming the bottle |
| Confirmed dimensions | If user provides height/width/depth/diameters, use them as strict proportion source | High for prompt quality | Dimensions override perspective distortion in uploaded photos |

## Taobao Water Bottle Slot Plan

| Slot | Goal | Recommended Content |
| --- | --- | --- |
| 1 | Click-through | Clean product hero, front or 45-degree, one core phrase max |
| 2 | Core value | Insulation/leak-proof/capacity/material, only confirmed facts |
| 3 | Details | Lid, seal ring, inner liner, straw, handle, mouth opening |
| 4 | Scenario/scale | Office, commuting, outdoor, school, car cup holder, hand scale |
| 5 | White background | Pure white product-only image |

## 1688

| Area | Working Rule | Confidence | Prompt Implication |
| --- | --- | --- | --- |
| Main image size | Square, at least 750 x 750 px; 800 x 800 safe | Medium | Default export `1:1, 800 x 800 or 1000 x 1000` |
| Main image count | No fewer than 3 commonly stated; 5 recommended | Medium | Build 5 slots for MVP |
| White-background image | Fifth image often recommended as white-background | Medium | Keep slot 5 clean |
| Main image content | Real product image, clear, centered, not pure text | Medium | Product readability beats decoration |
| Logo | Small corner logo may be acceptable; avoid covering product | Low-medium | Use only when user provides brand logo |
| GIF | New main/SKU images should avoid GIF | Medium | Static image prompts only |
| Detail image width | Public guidance often mentions mobile-friendly 750 px+ or around 790 px width | Medium | Use modular detail images, not one giant image |
| Forbidden elements | Blurry/overexposed/distorted product, contact info, external traffic, exaggerated claims, non-brand watermarks | Medium-high | Add to negative prompt |
| Product proportion | Product must keep source-photo geometry inside target canvas | High for prompt quality | Add whitespace instead of stretching or widening the bottle |
| Confirmed dimensions | If user provides height/width/depth/diameters, use them as strict proportion source | High for prompt quality | Dimensions override perspective distortion in uploaded photos |

## 1688 Water Bottle Slot Plan

| Slot | Goal | Recommended Content |
| --- | --- | --- |
| 1 | B2B hero | 45-degree/front product hero, clean background, sourcing trust |
| 2 | SKU/series | Colors, capacities, lid variants, packaging variants |
| 3 | Parameters | Capacity, dimensions, material, weight, verified performance |
| 4 | Detail/process | Leak-proof lid, inner liner, straw, handle, coating, packaging |
| 5 | White background | Product-only clean white image |

## Key Difference: Taobao vs 1688

Taobao prompt direction:

- consumer conversion;
- thumbnail attractiveness;
- clean premium feel;
- restrained text;
- lifestyle trust;
- white-background fifth image.

1688 prompt direction:

- factory/trade procurement;
- product parameters;
- SKU completeness;
- OEM/ODM/customization when true;
- packaging, supply ability, and buyer confidence;
- slightly more information density in secondary images.

## Product Proportion Rule

For both Taobao and 1688, the platform canvas ratio does not define the product shape. A square 800 x 800 or 1000 x 1000 main image is only the outer canvas.

Prompt implication:

- Preserve the uploaded product's height-to-width ratio.
- Preserve cup body thickness, lid size, top/bottom width relation, handle/straw position, and silhouette.
- Use whitespace to fit the product into a square canvas.
- Do not stretch, squash, slim, widen, or redesign the product so it fills the canvas.
- Add a `Proportion lock` line to every image prompt.

Dimension handling:

- If product dimensions are missing, ask the user once for height, width, depth, top diameter, bottom diameter, body diameter, lid height, handle/straw dimensions, and capacity.
- If the user chooses to continue without dimensions, generate from current image evidence and label proportions as `视觉估算，需复核`.
- If dimensions are provided, use them as the strict geometry source for every image angle.
- Photos remain references for material, color, logo, surface texture, structure, and detail layout, but dimensions override perspective distortion.

## Source URLs

- https://www.biaojixia.com/blog/taobao-main-image-requirements-guide
- https://www.10100.com/article/1152704
- https://www.pjx666.com/BBS/Details?id=388
- https://www.10100.com/article/32534884
- https://m.maijiaw.com/article/527778
