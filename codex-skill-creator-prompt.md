请基于当前仓库继续完善 `interview-project-qa-skill`，重点围绕以下目标：

1. 保持“先 diarization，再 transcription”的主流程不变。
2. 保持两人面试场景：interviewer / candidate。
3. 继续强化长音频稳定性：
   - 允许配置 chunk merge / split 参数
   - 增加更稳的失败重试与中间缓存
   - 补充 1h~2h 样本的回归测试
4. 继续强化项目问题分类器：
   - 为 architecture / optimization / debugging / tradeoff 提供更高优先级排序
   - 为 collaboration / conflict_resolution / business_impact 提供更稳的召回
   - 增加 extraction 评测样例
5. 继续强化 Notion 写入：
   - 保持本地 Markdown 导出
   - 保持 Notion REST API markdown create / replace path
   - 保持 Notion hosted MCP path
   - 为 API 与 MCP 分别增加更清晰的错误处理与日志
6. 不要删除现有 CLI；在此基础上增强。
7. 所有模型输入输出继续使用 Pydantic schema。
8. 所有 prompt 修改都要同步更新 `prompts/` 与 `README.md`。

额外要求：
- 优先保证 CLI 可运行和导出链路稳定。
- 不要伪造候选人经历；扩写必须在 `expansion_notes` 中诚实标记。
- 对于 Notion API，优先使用 markdown content APIs，而不是低层 block API。
- 对于 Notion MCP，默认使用 hosted MCP server，并假设 access token 已由外部 OAuth 流程提供。
