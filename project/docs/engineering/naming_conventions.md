# 命名规范（v0.1）

## 文件与目录
- Python 文件: snake_case.py。
- 文档文件: 小写英文 + 下划线，如 user_flows.md。
- 目录名: 小写英文，语义明确。

## 代码符号
- 类名: PascalCase。
- 函数/变量: snake_case。
- 常量: UPPER_SNAKE_CASE。
- 私有成员: 前缀 _。

## 测试命名
- 测试文件: test_<module>.py。
- 测试函数: test_<行为>_<预期结果>()。
- 用例描述应包含输入条件与期望。

## 文档命名
- 需求文档: PRD.md。
- 架构文档: architecture.md。
- 规范文档统一放 docs/engineering。

## 禁止项
- 禁止使用拼音缩写和无语义短名。
- 禁止同一概念多种命名（如 score/sheet 混用）。
