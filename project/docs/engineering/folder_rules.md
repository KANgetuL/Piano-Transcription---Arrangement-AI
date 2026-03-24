# 文件结构规则（v0.1）

## 源码目录规则
- src/app: 应用入口、流程编排、启动配置。
- src/components: UI 组件，不含复杂业务规则。
- src/services: 外部系统与模型适配层。
- src/models: 领域对象与数据结构。
- src/utils: 无业务状态的通用工具函数。
- src/config: 配置定义与加载。

## 文档目录规则
- docs/product: 产品目标、功能与路线。
- docs/ux: 用户路径、页面与边界场景。
- docs/ui: 视觉规范与设计 token。
- docs/engineering: 架构与工程规范。
- docs/aidoc: AI 协作上下文、状态与日志。

## 数据与测试规则
- data/schemas: 数据模型与约束说明。
- data/mock: 测试或演示样本数据。
- data/migrations: 迁移脚本或迁移记录。
- tests/unit|integration|e2e: 按测试层级分类。

## 变更规则
- 新增目录前先确认是否可复用现有目录。
- 不同职责代码不得混放。
- 文件移动需同步更新相关文档引用。
