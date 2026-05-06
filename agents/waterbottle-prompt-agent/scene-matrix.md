# Water Bottle Scene Matrix

Use this matrix to recommend scene-image options after identifying the uploaded bottle type.

## Default Rules

- Scene images are mandatory in a complete image set.
- The agent should infer bottle type from product photos and facts, then offer 4-8 scene options.
- User can choose 1-2 scenes. If the user skips selection, use the strongest default for the platform and bottle type.
- Scene images must preserve product geometry, dimensions, SKU consistency, color, lid structure, handle/straw position, and material.
- The product should remain the visual hero. Background and props only support the use case.

## Scene Matrix

| Bottle Type | Taobao Scenes | 1688 Scenes |
| --- | --- | --- |
| 保温杯 | 通勤手持、办公桌、车载杯架、冬季热饮、礼品开箱 | 商务礼品、企业定制、办公采购、包装出货、工厂质检 |
| 咖啡杯 | 咖啡桌、车载通勤、办公键盘旁、城市早晨、轻商务 | 咖啡连锁采购、礼品定制、Logo定制、包装展示 |
| 运动水杯 | 健身房、跑步后补水、瑜伽垫旁、骑行包侧袋、户外运动 | 运动渠道批发、户外用品采购、大容量参数、耐用细节 |
| 儿童水杯 | 书包侧袋、课桌、亲子出行、儿童餐桌、卡通生活方式 | 学校团购、儿童用品渠道、包装安全、颜色SKU |
| 塑料杯 | 校园、办公室冷饮、户外轻便、包内便携、夏季清爽 | 轻量批发、颜色系列、材质展示、超市货架 |
| 玻璃杯 | 茶水/水果茶、办公桌、居家厨房、健康饮水、女性生活方式 | 礼品套装、材质透明展示、包装、批发系列 |
| 大容量吨吨杯 | 健身房、户外补水、桌面容量对比、运动包旁、夏季运动 | 大容量卖点、运动渠道、容量刻度、颜色SKU |
| 礼品定制杯 | 礼盒开箱、办公礼赠、节日礼物、企业活动 | OEM/ODM、Logo打样、包装、批量出货 |
| 户外露营杯 | 露营桌、山野徒步、车后备箱、营地咖啡、岩石/木桌 | 户外渠道、耐用细节、包装、批量采购 |
| 吸管杯 | 通勤、健身、女性桌面、车载杯架、夏季冷饮 | 颜色SKU、吸管结构、渠道批发、包装 |

## Scene Prompt Snippet

Chinese:

```text
场景相关性：场景必须符合该水杯类型和目标买家使用逻辑。产品是画面主角，背景和道具只用于说明使用场景，不能改变、遮挡或弱化产品。保持产品真实比例、颜色、材质、杯盖结构、手柄/吸管位置和所有SKU一致性。
```

English:

```text
Scene relevance: the scene must logically match the identified bottle type and buyer persona. Keep the product as the visual hero; props and background support the use case without changing, hiding, or weakening the product. Preserve the real product proportions, color, material, lid structure, handle/straw position, and SKU consistency.
```

