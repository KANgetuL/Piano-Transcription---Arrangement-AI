project/
│
├─ src/                        # 实际源码
│  ├─ app/                     # 主程序
│  ├─ components/              # UI组件
│  ├─ services/                # API / 服务
│  ├─ utils/                   # 工具函数
│  ├─ models/                  # 数据结构
│  └─ config/                  # 项目配置
│
├─ docs/                       # 项目文档
│  ├─ product/                 # 产品文档
│  │  ├─ PRD.md                # 产品需求文档
│  │  ├─ features.md           # 功能列表
│  │  └─ roadmap.md            # 产品路线
│  │
│  ├─ ux/                      # 用户路径
│  │  ├─ user_flows.md         # 用户导航路径
│  │  ├─ screens.md            # 页面说明
│  │  └─ edge_cases.md         # 用户边界情况
│  │
│  ├─ ui/                      # UI设计系统
│  │  ├─ typography.md
│  │  ├─ colors.md
│  │  ├─ spacing.md
│  │  ├─ components.md
│  │  └─ tokens.json
│  │
│  ├─ engineering/             # 工程规范
│  │  ├─ architecture.md       # 系统架构
│  │  ├─ coding_standards.md   # 编码规范
│  │  ├─ naming_conventions.md # 命名规则
│  │  ├─ dependency_rules.md   # 包管理
│  │  └─ folder_rules.md       # 文件结构规则
│  │
│  ├─ aidoc/                      		# AI专用文档
│   |  ├─ ai_rules.md           # AI必须遵守的规则
│   |  ├─ ai_context.md         # AI上下文说明
|	|	├─ logs/                       # AI操作记录
|	|	│  ├─ operations.md            # 操作日志
|	|	│  └─ errors.md                # 错误记录
|	|	├─ state/                      # AI状态
|	|	│  ├─ progress.md              # 当前项目进度
|	|	│  ├─ context.md               # 当前上下文
├─ data/                       # 数据定义
│  ├─ schemas/                 # 数据结构
│  │  └─ database_schema.md
│  │
│  ├─ mock/                    # mock数据
│  │  └─ sample_data.json
│  │
│  └─ migrations/              # 数据迁移
│
│
├─ tests/                      # 测试
│  ├─ unit/
│  ├─ integration/
│  └─ e2e/
│
├─ README.md
├─ package.json / pyproject.toml
└─ .gitignore