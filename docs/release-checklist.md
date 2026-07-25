# Release checklist

更新时间：2026-07-24。

## 当前已验证

- [x] 候选框架在独立目录中重新实现，不继承私有仓 Git 历史；
- [x] 后端、工作流和模型合同测试通过；
- [x] 前端 TypeScript 检查和生产构建通过；
- [x] 从不带 `.venv`、`node_modules`、`dist` 和 `runtime` 的干净副本重新安装成功；
- [x] 模拟任务可以生成并保存产物；
- [x] 配置模型分支通过真实本地 HTTP 兼容接口端到端测试；
- [x] 浏览器验证桌面与手机布局无横向溢出；
- [x] 页面刷新后 SQLite 产物仍存在；
- [x] 当前候选公开文件未发现私有品牌词、本机绝对路径、密钥格式或业务数据文件；
- [x] 已生成前后端主要依赖许可证清单。
- [x] 公共文件 allowlist 校验和可复现源码 ZIP 已生成；
- [x] 从源码 ZIP 重新安装依赖、构建前端、运行测试和启动探测成功。
- [x] GitHub Release 工作流已通过 YAML 解析、正确标签和错误标签保护验证；
- [x] 发布包 SHA-256 校验文件与 ZIP 内容一致。
- [x] CI 与 Release 均已配置 Docker Compose 构建、健康检查和首页探测；

## 公开前仍需完成

- [ ] 在真实 Docker 环境执行 `docker compose up --build`；
- [ ] 用发布者提供的一次性测试密钥完成真实模型调用，密钥不得写入仓库；
- [ ] 仓库所有者审核 README、预览图、项目名称和对外承诺；
- [ ] 确认安全联系渠道并更新 `SECURITY.md`；
- [ ] 对待提交文件执行最终 allowlist；
- [ ] 创建全新的 Git 仓库和首次提交；
- [ ] 再次执行密钥、PII、绝对路径和大文件扫描；
- [ ] 获得明确公开授权后创建 GitHub 公共仓库；
- [ ] 公共仓库中的 CI 与 Release 工作流首次实际运行通过；
- [ ] 从 GitHub 下载 ZIP，在另一目录做最终安装检查；
- [ ] 未登录窗口检查 README、LICENSE、源码与 Releases。

## 首次提交 allowlist

只允许：

```text
.github/
apps/
configs/
data/demo/
docs/
scripts/
tests/
workflows/
.dockerignore
.env.example
.gitignore
CHANGELOG.md
CONTRIBUTING.md
Dockerfile
LICENSE
PROVENANCE.md
README.md
SECURITY.md
THIRD_PARTY_NOTICES.md
TRADEMARKS.md
docker-compose.yml
```

明确禁止：

```text
.env
.venv/
node_modules/
dist/
runtime/
release/
*.db
*.duckdb
*.csv
*.xls
*.xlsx
私有仓历史
真实客户、订单和经营数据
```
