# 数据结构定义（v0.1）

## 目标
定义音频任务、谱面结果与导出记录的最小数据结构，供本地存储或后续云端扩展复用。

## 实体: transcription_task
- id: string (uuid)
- source_path: string
- source_format: string (mp3|wav)
- duration_sec: number
- mode: string (normal|pop|electronic|classical|black)
- status: string (queued|running|paused|canceled|failed|done)
- progress: number (0-100)
- created_at: datetime
- updated_at: datetime

## 实体: score_document
- id: string (uuid)
- task_id: string (fk -> transcription_task.id)
- title: string
- tempo_bpm: number
- key_signature: string
- time_signature: string
- bars: number
- notes_json: json
- created_at: datetime

## 实体: export_record
- id: string (uuid)
- score_id: string (fk -> score_document.id)
- format: string (mid|musicxml|pdf|png)
- output_path: string
- result: string (success|failed)
- created_at: datetime

## 约束
- transcription_task.status 与 progress 保持一致性。
- export_record 仅允许已完成 score_document 导出。
- notes_json 字段结构需与领域模型版本号绑定。
