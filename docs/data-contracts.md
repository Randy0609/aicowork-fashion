# Data contracts

本文记录 v0.1-alpha 对外稳定程度最高的数据合同。示例内容均为模拟数据。

## 运行商品内容工作流

`POST /api/workflows/product-content/run`

请求：

```json
{
  "provider": "demo",
  "inputs": {
    "category": "女装上衣",
    "product_name": "云感针织短袖",
    "material": "材质比例待商家核对",
    "target_customer": "关注通勤舒适度的人群",
    "selling_points": "圆领基础版型；袖口采用罗纹收边",
    "tone": "克制专业"
  }
}
```

`provider`：

- `demo`：确定性模拟结果，不访问外部模型；
- `configured`：使用服务器环境变量配置的模型。

成功响应：

```json
{
  "task": {
    "id": "task_...",
    "workflow_id": "product-content",
    "provider": "demo",
    "status": "completed",
    "artifact_id": "artifact_..."
  },
  "artifact": {
    "id": "artifact_...",
    "workflow_id": "product-content",
    "title": "云感针织短袖 · 商品内容",
    "content": {
      "product_title": "云感针织短袖｜女装上衣",
      "selling_points": [
        "圆领基础版型",
        "袖口采用罗纹收边"
      ],
      "social_post": "待人工审核的内容草稿",
      "short_video_script": [
        {
          "scene": "开场",
          "visual": "展示商品整体",
          "voiceover": "介绍商品"
        }
      ],
      "review_notes": [
        "发布前核验商品事实"
      ],
      "generation_mode": "demo"
    }
  }
}
```

## 错误合同

- `404`：工作流、任务或产物不存在；
- `422`：输入缺少必填字段或不符合合同；
- `400`：请求使用真实模型，但服务器配置不完整；
- `502`：模型服务失败或返回无法解析的内容；
- `500`：未预期的本地执行错误。

错误响应不会返回 API Key。

## 工作流清单

`GET /api/workflows`

只返回公开清单，不返回 Python 处理器入口。部署者可以用它动态生成其他前端或管理界面。

## 品类配置

`GET /api/categories`

品类配置只负责字段提示和演示资料，不应包含真实企业的商品库或内部经营数据。
