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

### notes_json 结构（v0.1）
- schema_version: string
- segments: AudioSegment[]
- note_events: NoteEvent[]
- chord_events: ChordEvent[]

### AudioSegment
- segment_id: string
- start_sec: number
- end_sec: number
- sample_rate: number

### NoteEvent
- pitch_midi: integer (0-127)
- velocity: integer (1-127)
- start_sec: number
- end_sec: number
- hand: string (left|right|auto)

### ChordEvent
- symbol: string
- start_sec: number
- end_sec: number

## 协议: transcription_request（模型输入）
- task_id: string
- source_path: string
- mode: string (normal|pop|electronic|classical|black)
- sample_rate: number

## 协议: transcription_result（模型输出）
- task_id: string
- title: string
- tempo_bpm: number
- key_signature: string
- time_signature: string
- bars: number
- segments: AudioSegment[]
- notes: NoteEvent[]
- chords: ChordEvent[]

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
- 任意 NoteEvent 必须满足 start_sec < end_sec。
- 任意 AudioSegment 必须满足 start_sec < end_sec 且 sample_rate > 0。
