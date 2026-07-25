# GitHub release process

本文只记录正式公开后的发布步骤。创建公共仓库、首次推送和打标签都属于外部写操作，必须由仓库所有者明确授权。

## 首次公开

1. 在独立候选目录执行：

   ```bash
   python scripts/verify_public_tree.py
   pytest -q
   cd apps/web && pnpm install --frozen-lockfile && pnpm build && cd ../..
   python scripts/smoke_boot.py --require-web
   ```

2. 只按 [release checklist](release-checklist.md) 的 allowlist 创建首次提交。
3. 创建全新公共仓库，不修改任何私有仓库的可见性。
4. 推送 `main` 后等待 CI 通过。
5. 从公共仓库下载 ZIP，在另一个目录复核安装。

## 创建 v0.1.0-alpha Release

本仓库的 `release.yml` 只在标签推送后运行。

```bash
git tag -a v0.1.0-alpha -m "AiCowork Fashion v0.1.0-alpha"
git push origin v0.1.0-alpha
```

工作流会依次：

1. 校验公共文件 allowlist；
2. 运行后端、工作流、模型合同和发布包测试；
3. 安装并构建前端；
4. 通过本地 HTTP 兼容模型服务跑通配置模型链路；
5. 启动后端并探测健康检查和首页；
6. 使用 Docker Compose 构建容器并探测健康检查和首页；
7. 生成可复现源码 ZIP；
8. 生成 SHA-256 校验文件；
9. 创建 GitHub prerelease 并上传两个文件。

如果源码中的版本号与标签不一致，发布脚本会拒绝继续。

## 下载者获得什么

GitHub Release 提供：

- `aicowork-fashion-0.1.0-alpha.zip`
- `aicowork-fashion-0.1.0-alpha.zip.sha256`

GitHub 自带的 Source code ZIP 仍然存在，但推荐商家和技术服务商下载经过 allowlist 生成的发布包。
