# 组件规范（v0.1）

## 按钮
- 类型: Primary、Secondary、Danger、Ghost。
- 状态: default、hover、active、disabled、loading。

## 输入组件
- 文本输入: 支持校验态（success/warning/error）。
- 文件上传: 支持拖拽态、进度态、失败重试态。

## 进度组件
- 线性进度条用于扒谱进度。
- 必须显示百分比与剩余时间估计。

## 预览组件
- 乐谱画布支持缩放、拖拽、当前播放位置高亮。

## 反馈组件
- Toast: 短时提示。
- Dialog: 高风险确认（取消任务、覆盖导出）。
- Inline Error: 表单与上传区域即时错误提示。
