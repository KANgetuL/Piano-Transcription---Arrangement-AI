agent模式下AI必须严格遵守以下规则，并按照顺序完成规则包含的任务：
0.若以下规则存在冲突，优先级为「错误记录（errors.md）> 工程规范 > 任务执行 > 日志记录」；未明确的场景，AI 需先向用户确认后再执行。状态检索仅针对当前任务的直接前驱任务，不全局检索非规范状态关键词（如 task_completed应搜索TODO,DONE）
1.阅读aidoc文件夹下的ai_rules.md（本文件），项目环境conda311
2.阅读ai_context.md，了解AI上下文信息
3.读取aidoc下的state文件夹中的progress.md。该文件规划了项目进度，并用DONE和TODO区分了是否完成了进度。优先读取 docs/product/PRD.md 和 roadmap.md，再按需读取 ux/engineering 下的核心文档（如 user_flows.md、architecture.md）。注意：读取文档时，仅提取「项目目标、核心功能、当前阶段里程碑、技术栈约束」等关键信息，无需读取文档全文
4.读取ai_doc下的logs文件夹中的operations.md和errors.md。然后单次对话只进行一个任务（一个任务指「用户单次对话中明确提出的单一目标」（如 “编写一个登录接口”“修复支付模块 bug”）），完成任务后在tests生成临时测试文件(临时测试文件命名规范为「test_任务名称_时间戳。后缀」，测试内容需匹配 engineering/coding_standards.md 中的测试规范；测试结束的触发条件为「AI 完成测试用例执行并输出结果」)，无论测试结果是否通过都在测试结束删除临时测试文件。若任务未完成仍然标记TODO，并将错误情况与可能的错误原因按记录时间记录在errors.md（应在文件底部）。若任务完成标记DONE，并将代码修改简略摘要和修改摘要按时间填入operations.md（应在文件底部）。这一步结束后将上下文中关键节点（关键节点定义为「任务启动时间、核心操作动作、结果标记（DONE/TODO）、错误类型（如有）」）和对话时间按照时间先后记录在ai_context.md中（应在文件底部）
5.严格按照engineering/文件夹下的规范，规范优先级：architecture.md> coding_standards.md > naming_conventions.md > 其他，冲突时按优先级执行
6.若指定路径文件缺失 / 读取失败，立即将错误信息记录至 errors.md，并向用户反馈缺失文件名称 + 路径，等待用户补充后再执行后续步骤
7.如果单次对话提交实验性代码或实验性功能（可能带来不稳定因素），有必要向用户提示创建新分支