# Contributing

AiCowork Fashion 当前处于 alpha 阶段，优先接受以下贡献：

- 新的服饰细分品类配置；
- 不编造商品事实的内容工作流；
- 安装、兼容性和无障碍修复；
- 可复现的安全问题与测试。

## 本地检查

```bash
source .venv/bin/activate
pytest -q

cd apps/web
pnpm install --frozen-lockfile
pnpm build
```

提交内容不得包含 API Key、客户资料、订单明细、真实经营数据或无明确授权的品牌素材。

贡献者提交代码即表示其有权提交该内容，并同意按仓库许可证发布。公开仓建立后会补充正式的 DCO 签署方式和 Issue 模板。
