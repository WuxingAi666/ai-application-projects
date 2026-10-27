# 部署位置与操作说明

## 1. 最终访问方式

网站继续使用 https://wuxingai666.github.io/wx-portfolio/ 。
例如后端使用 https://assistant.你的域名 ，浏览器通过 HTTPS 调用它。
后端域名、服务器系统、现有反向代理情况仍需你提供后才能最终落配置。

本方案按 Linux x86_64、Docker Engine 和 Compose v2 设计；建议至少 2GB 内存。
默认使用远程模型，不需要 GPU。本地 BGE 需要额外依赖和更大内存。

## 2. 云服务器上传哪些文件

将成品包中的 backend/、deploy/、scripts/ 放在同一个父目录，例如：

    /opt/wx-rag/
      backend/
      deploy/
      scripts/

不要上传 frontend 到 API 容器；网站继续由 GitHub Pages 提供。
不要把 backups、旧项目或开发日志放进服务器网站目录。

## 3. DNS、端口与已有站点

给后端子域名添加 A 记录，指向服务器公网 IP。
有 IPv6 AAAA 记录时也必须指向能服务此域名的正确地址，避免随机失败。
服务器防火墙、安全组放行 80、443。

如果服务器已有宝塔、Nginx、Caddy 或其他网站占用了 80/443，
不要直接启动默认 Caddy 服务抢端口，使用本文最后的“复用现有反向代理”方案。
大陆服务器绑定域名需满足服务商的备案要求；域名是否已备案需实际确认。

## 4. 私有配置

在服务器项目根目录：

    cp backend/.env.example backend/.env
    cp deploy/.env.example deploy/.env

编辑 backend/.env：

    DEEPSEEK_API_KEY=新Chat密钥
    EMBEDDING_API_KEY=新Embedding密钥
    EMBEDDING_PROVIDER=siliconflow
    EMBEDDING_API_MODEL=BAAI/bge-m3

编辑 deploy/.env：

    API_DOMAIN=assistant.你的域名
    ACME_EMAIL=你的邮箱
    SITE_ORIGIN=https://wuxingai666.github.io
    PUBLIC_SITE_URL=https://wuxingai666.github.io/wx-portfolio/

生成内部随机管理凭据，在项目根目录执行：

    python3 scripts/init-secrets.py
    chmod 600 backend/.env deploy/.env

脚本在 backend/.env 中生成 ADMIN_TOKEN 和 RATE_LIMIT_SALT，不会显示它们。
生产模式会检查这两项，并拒绝使用开发默认值。
请在服务器填入替换过的模型密钥；原密钥曾在聊天中出现过。

## 5. 启动后端与 HTTPS

在 deploy 目录执行：

    docker compose --env-file .env config --quiet
    docker compose --env-file .env up -d --build
    docker compose ps
    docker compose logs --tail 100 api

首次启动会读取公开资料并调用 Embedding API 建库。
API 主进程先启动，/health/ready 在索引就绪后才返回 200。
Caddy 自动申请证书，DNS 和端口必须先准备正确。

    curl -f https://assistant.你的域名/health/ready

返回 status=ready 后再接前端。生产环境默认关闭 /docs。
不要将 API 容器的 8000 端口额外发布到公网。
容器信任代理头的前提是只有受控的 Caddy 能访问其端口；不要绕过这个网络边界。

## 6. 发布网站前端

修改 frontend/js/assistant-config.js：

    apiBase: "https://assistant.你的域名"

地址使用 HTTPS、不带 /api 后缀；组件会自动拼接接口路径。
GitHub Pages 的 HTTPS 页面不能正常调用普通公网 HTTP 后端。

将 frontend/ 里的 index.html、css、js、assets、.nojekyll 等放到现有
wx-portfolio 仓库根目录。保留原仓库 .git，不要用成品目录覆盖仓库本身。
先在 Git 分支检查修改，再提交并推送到现有发布分支。

backend、deploy、.env、备份和运行数据都不能放进 GitHub Pages 根目录。
CORS 来源为 https://wuxingai666.github.io，不包含 /wx-portfolio/ 路径。
同一 GitHub Pages 域名下其他页面共享此 Origin，所以 CORS 不能做页面级鉴权。

## 7. 用外网验收

- 打开网站、点开助手，状态显示在线。
- 提问“他的 RAG 项目是怎么实现的”，出现流式答案和可展开来源。
- 接着问“为什么这样做”，应延续同一项目。
- 问未记录的具体工作承诺或私人信息，不能编造。
- 两个不同浏览器的对话互不串话。
- 停止生成、新对话、手机全屏、来源跳转正常。
- 停止或重启后端时，个人网站本身仍可浏览并能查看简历。
- 关掉你的个人电脑，外网仍可问答。

## 8. 更新知识、备份与回滚

修改 backend/data/public/ 中的 TXT 和 manifest.json；
同步网站介绍，避免出现两套事实。

    docker compose --env-file .env up -d --build api

新容器启动时计算指纹，知识或模型配置变化会生成新索引。
服务运行中不自动读取你 Windows 电脑上的文件。线上知识必须上传并重新部署。
不开放网页上传和公开重建接口，避免访客改写本人资料。

备份知识源文件、私有环境变量、rag-storage 数据卷。
不要使用 docker compose down -v，否则会删除持久化额度与索引。
回滚时恢复上一份代码与知识文件再重建镜像；旧索引以指纹保存，可重新加载。

查看日志：

    docker compose logs --tail 100 api

查看管理统计：

    curl -H "Authorization: Bearer 你的ADMIN_TOKEN" https://assistant.你的域名/api/v1/admin/stats

只在自己的终端中操作，ADMIN_TOKEN 不写进浏览器、不分享给访客。
数据保存近 30 天，仅包含匿名化 IP 哈希、请求 ID、时间、状态和生成 Token 计数。
Token 计数不是账单，未覆盖改写调用和部分失败请求；实际费用以提供商账单为准。

## 9. 复用现有反向代理

有现有 Nginx/宝塔时，在 deploy 目录使用：

    docker compose --env-file .env -f compose.existing-proxy.yaml up -d --build

此方案只把 API 发布在服务器回环地址 127.0.0.1:8010，
由现有 HTTPS 站点代理。Nginx location 示例见 nginx-location.conf。
证书与域名由现有面板或代理维护，不再运行 Caddy。

首次发布仍需要在真实服务器验证 Docker 构建、证书和跨域；本地 Windows
没有 Docker，因此交付验收不声称已完成 Linux 容器运行验证。
