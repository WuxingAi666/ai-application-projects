# 仵星 · AI 应用与全栈实践

[个人作品集](https://llywjr.love/wx/) · [记账本在线体验](https://wuxingai666.github.io/xiaozhangben/)

围绕业务需求、模型/API 集成、前后端交互和迭代交付整理六个个人项目。保留真实实现和研发状态，不以未经验证的数字替代效果证据。开发过程中使用 AI 辅助编码、调试与文档整理。

| 顺序 | 项目 | 当前材料 |
| --- | --- | --- |
| 01 | [个人作品集网站 × RAG 智能问答助手](projects/portfolio-rag) | 全栈实现 · 统一云端部署 |
| 02 | [中文语音情感分析系统](projects/speech-emotion) | 应用原型 · 评测待完善 |
| 03 | [BOSS 求职辅助与本地监控工具](projects/boss-assistant) | 源码公开 · 个人技术实践 |
| 04 | [仵星的记账本](projects/ledger) | 已上线 · 本人持续使用 |
| 05 | [果蔬成熟度识别与语音采摘辅助](projects/fruit-ripeness) | 项目经历 · 暂不提供源码 |
| 06 | [Coze 智能体与知识库问答实践](projects/coze-practice) | 基础搭建与了解 |

## 推荐阅读

先看 RAG 的架构说明、API、边界测试和部署配置，再看语音项目的前后端结构与模型接入状态、BOSS 工具的浏览器/API/SSE 集成及记账本的持续迭代。果蔬与 Coze 当前仅有说明，不作为已开源的可运行系统。

## 运行与配置

各项目分别创建独立环境，按各目录 README 运行。RAG 的网站与 API 统一部署到自有云服务器，Nginx + systemd 运行，完整主仓库为 https://github.com/WuxingAi666/wx-portfolio 。本网站已关闭 GitHub Pages；记账本的独立 Pages 不受影响。实际公网验收状态见 projects/portfolio-rag/docs/PROJECT-STATUS.md。所有密钥通过本机或服务器配置，仓库不含 .env、访客数据、音频、训练集、模型权重和企业内部材料。

原项目缺陷和未完成项在各目录明确记录；本次整理不等同于所有算法已完成验证或所有项目已生产上线。BOSS 目录沿用原项目 LICENSE，其他目录未单独授予开源许可，源码公开用于作品展示。
