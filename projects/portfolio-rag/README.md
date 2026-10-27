# 仵星的作品集 RAG 问答助手 · 交付版

个人网站与「仵星的RAG问答助手」组成完整全栈作品，配套独立的 LangChain + FAISS + FastAPI 后端。
悬浮入口名为「问问仵星的RAG问答助手」，通过提示语引导访客了解项目、实习与技术方案。
网站保留蓝色风格，内容围绕业务分析、编码实现、全栈集成与沟通交付组织；助手使用墨绿与暖白配色。
桌面默认 400×600 小窗，支持标题栏拖动、八向尺寸调整、放大还原、最小化与对话保留，手机全屏。
默认使用硅基流动 BGE-M3 语义向量与 DeepSeek Chat。网站继续托管在 GitHub Pages，
后端部署在你自己的云服务器。公网发布需要补上后端域名和服务器配置。

## 交付内容

| 目录 | 用途 | 部署位置 |
| --- | --- | --- |
| frontend/ | 网站完整源码、原图片、新聊天组件、RAG 展示卡片 | GitHub Pages 仓库根目录 |
| backend/ | Python API、公开知识 TXT、检索和生成、额度记录 | 云服务器，Docker 容器 |
| deploy/ | Docker Compose、Caddy 自动 HTTPS、现有反向代理方案 | 同一台云服务器 |
| scripts/ | 本地启动、内部密钥初始化、检查与打包 | 开发电脑或服务器 |
| docs/ | 部署、架构、知识维护和验收说明 | 自己查阅，不放进网站根目录 |
| backups/ | 原网站完整备份、旧 RAG 源码备份 | 只在本机保留，不公开上传 |
| output/ | 本地截图、评估结果、校验报告 | 本地验收记录 |

**模型密钥只存在 backend/.env。交付压缩包不包含任何真实密钥。**
开发目录已复用你原来的模型配置供本地验收；上传服务器时请通过私有方式配置。

## 本地运行

推荐 Windows Python 3.13，当前交付使用 Python 3.13.5 实际运行。
在 backend 目录创建独立环境并安装：

    python -m venv .venv
    .\.venv\Scripts\python -m pip install -r requirements.txt

首次解压的人需要复制 backend/.env.example 为 backend/.env，填写两枚模型密钥。
开发工作目录已经有配置时不要覆盖。

在成品根目录执行：

    powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1

网站 http://127.0.0.1:8931/ ，API 文档 http://127.0.0.1:8010/docs 。
脚本会输出两个进程 PID 和停止命令；日志写在 output/。
也可以分别开两个终端执行：

    cd backend
    python main.py

    cd frontend
    python -m http.server 8931 --bind 127.0.0.1

## 主要能力

- 原生、无 CDN 依赖的聊天组件；流式回答、停止、重试、新对话、来源展开、手机全屏。
- TextLoader 按清单加载公开 TXT，RecursiveCharacterTextSplitter 重叠分块。
- 远程 BGE-M3，或可选本地 BGE；FAISS 归一化向量语义召回。
- 最近对话补全检索问题，避免“这个项目”丢失主题。
- 资料不足时说明，提示词约束真实事实，回答附公开资料标记。
- 无 pickle 的索引持久化、内容指纹、文件完整性校验。
- SQLite 持久化单 IP / 全局请求额度、并发预约、UTC 日期重置。
- 无公开索引写接口；管理统计单独鉴权；错误输出去内部信息。
- Docker 非 root、API 不直接暴露公网、Caddy HTTPS、SSE 不缓冲。

## 验证

离线边界测试，不消耗模型 API：

    cd backend
    python -m unittest discover -s tests -v

真实召回及生成样例评估，会消耗模型 API：

    python evaluate.py

结果写到 output/evaluation.json。小样本结果不能当成泛化准确率。
阅读 docs/VALIDATION.md 查看本次实际验证的范围。项目文案统一维护在 frontend/content/projects.json，通过 scripts/sync-project-content.py 同步网站、简历与项目知识库。

## 公网部署

请按 docs/DEPLOYMENT.md 操作。关键步骤：

1. 后端子域名解析到云服务器，准备 80/443 端口或复用现有代理。
2. 在服务器配置 backend/.env 与 deploy/.env，生成内部管理密钥。
3. 在 deploy 目录运行 Docker Compose，确认 HTTPS 健康检查。
4. 把 frontend/js/assistant-config.js 的 apiBase 改成真实后端 HTTPS 地址。
5. 仅将 frontend/ 的内容发布到 GitHub Pages，不上传整个成品目录。
6. 从外部网络进行浏览器验收，再发送链接给面试官。

GitHub Pages 负责发布静态网站，后端需另行部署到云服务器。当前公网问答后端尚未接入，静态网站可独立浏览项目与简历。
