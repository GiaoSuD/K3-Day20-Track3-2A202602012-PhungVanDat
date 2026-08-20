# 📚 Lab 20: Multi-Agent Research System - Hướng Dẫn Thuyết Trình

## Tổng Quan Bài Lab

### 🎯 Mục Tiêu
Xây dựng một **hệ thống nghiên cứu đa tác tử (Multi-Agent)** có khả năng:
- Nhận câu hỏi từ người dùng
- Tìm kiếm và thu thập thông tin
- Phân tích và tổng hợp dữ liệu
- Viết câu trả lời cuối cùng

### 📊 So Sánh Hai Phương Pháp

| Khía Cạnh | Single-Agent | Multi-Agent |
|-----------|-------------|-------------|
| Định nghĩa | 1 agent làm tất cả | Nhiều agent chuyên biệt |
| Độ phức tạp | Đơn giản | Phức tạp hơn |
| Tốc độ | Nhanh hơn | Chậm hơn (có overhead) |
| Chất lượng | Khó kiểm soát | Có thể cao hơn |
| Debug | Khó | Dễ theo dõi từng bước |

---

## 🏗️ Kiến Trúc Hệ Thống

```
                    ┌─────────────┐
                    │  User Query │
                    └──────┬──────┘
                           │
                           ▼
                   ┌───────────────┐
                   │   Supervisor  │ ◄── "Đạo diễn" - Quyết định agent nào chạy tiếp
                   └───────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Researcher  │   │   Analyst   │   │    Writer   │
│  (Nghiên cứu)│   │  (Phân tích)│   │   (Viết)   │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  ▼
   research_notes    analysis_notes    final_answer
```

### 📝 Vai Trò Của Từng Agent

| Agent | Nhiệm Vụ | Đầu Ra |
|-------|----------|--------|
| **Supervisor** | Quyết định agent nào chạy tiếp theo | route_history |
| **Researcher** | Tìm kiếm thông tin, thu thập nguồn | sources, research_notes |
| **Analyst** | Phân tích, so sánh, đánh giá | analysis_notes |
| **Writer** | Viết câu trả lời hoàn chỉnh | final_answer |
| **Critic** *(bonus)* | Kiểm tra chất lượng, fact-check | quality_review |

---

## 🔧 Cấu Hình Môi Trường

### 1. Tạo Virtual Environment
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt (Windows)
.venv\Scripts\activate

# Kích hoạt (Mac/Linux)
source .venv/bin/activate
```

### 2. Cài Đặt Dependencies
```bash
# Cài đặt project với dependencies
pip install -e ".[dev,llm]"

# Hoặc cài riêng
pip install -e .
pip install openai langgraph langsmith
```

### 3. Cấu Hình API Key
```bash
# Copy file mẫu
cp .env.example .env

# Mở .env và điền API key
# OPENAI_API_KEY=sk-...your-key...
```

---

## 🚀 Chạy Các Lệnh Lab

### 1. Chạy Baseline (Single-Agent)
```bash
python -m multi_agent_research_lab.cli baseline `
    --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

**Giải thích:**
- Agent đơn lẻ nhận câu hỏi và trả lời trực tiếp
- Không có bước trung gian
- Nhanh nhưng khó kiểm soát chất lượng

### 2. Chạy Multi-Agent Workflow
```bash
python -m multi_agent_research_lab.cli multi-agent `
    --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

**Giải thích:**
```
User Query → Supervisor → Researcher → Analyst → Writer → Final Answer
                ↑
           Kiểm tra trạng thái
           - Đã có research? → Gọi Analyst
           - Đã có analysis? → Gọi Writer
           - Hoàn thành? → Dừng
```

### 3. So Sánh Benchmark
```bash
python -m multi_agent_research_lab.cli compare `
    --query "Research GraphRAG state-of-the-art"
    --output benchmark_report.md
```

---

## 📂 Cấu Trúc Code Quan Trọng

### State Management (`core/state.py`)
```python
class ResearchState(BaseModel):
    request: ResearchQuery        # Câu hỏi đầu vào
    iteration: int = 0           # Số lần lặp
    route_history: list[str]      # Lịch sử routing
    
    sources: list[SourceDocument]    # Nguồn tham khảo
    research_notes: str | None       # Ghi chú nghiên cứu
    analysis_notes: str | None       # Ghi chú phân tích
    final_answer: str | None         # Câu trả lời cuối cùng
    
    trace: list[dict]             # Log thực thi
    errors: list[str]             # Các lỗi gặp phải
```

### Supervisor Logic (`agents/supervisor.py`)
```python
def run(self, state: ResearchState) -> ResearchState:
    # Quy tắc routing:
    if not state.research_notes:
        return "researcher"      # Chưa nghiên cứu → Gọi Researcher
    elif not state.analysis_notes:
        return "analyst"         # Chưa phân tích → Gọi Analyst
    elif not state.final_answer:
        return "writer"          # Chưa viết → Gọi Writer
    else:
        return "done"            # Hoàn thành
```

### Workflow Orchestration (`graph/workflow.py`)
```python
def run(self, state: ResearchState) -> ResearchState:
    while state.iteration < max_iterations:
        # 1. Supervisor quyết định
        state = supervisor.run(state)
        
        # 2. Chạy agent được chọn
        if route == "researcher":
            state = researcher.run(state)
        elif route == "analyst":
            state = analyst.run(state)
        elif route == "writer":
            state = writer.run(state)
        elif route == "done":
            break
```

---

## 📈 Metrics Theo Dõi

| Metric | Cách Đo | Ý Nghĩa |
|--------|---------|---------|
| **Latency** | Thời gian wall-clock | Hiệu suất |
| **Cost** | Số token × giá | Chi phí API |
| **Quality** | Đánh giá peer review | Chất lượng đầu ra |
| **Citation Coverage** | Claims có nguồn / tổng | Độ tin cậy |
| **Failure Rate** | Lỗi / tổng queries | Độ ổn định |

---

## ❓ Câu Hỏi Thảo Luận

### 1. Khi nào nên dùng Multi-Agent?
✅ **Nên dùng khi:**
- Câu hỏi phức tạp, cần nghiên cứu sâu
- Cần trace được từng bước
- Yêu cầu chất lượng cao với citations
- Cần tái sử dụng agent cho nhiều task

❌ **Không nên dùng khi:**
- Câu hỏi đơn giản, cần trả lời nhanh
- Hạn chế về budget
- Không cần theo dõi chi tiết

### 2. Làm sao Supervisor quyết định đúng?
Supervisor kiểm tra `ResearchState`:
```python
# Còn thiếu gì?
if missing("research_notes"):
    call("researcher")
elif missing("analysis_notes"):
    call("analyst")
elif missing("final_answer"):
    call("writer")
else:
    stop()
```

### 3. Tại sao cần Shared State?
```
┌─────────────────────────────────────────┐
│           Shared ResearchState          │
├─────────────────────────────────────────┤
│  request: "GraphRAG là gì?"             │
│  sources: [doc1, doc2, doc3]           │
│  research_notes: "GraphRAG = Graph + RAG│
│  analysis_notes: "Ưu điểm:..."          │
│  final_answer: "GraphRAG là..."         │
└─────────────────────────────────────────┘
         ▲                    ▲
    Researcher ghi        Writer đọc
```

---

## 🛡️ Guardrails (Bảo Vệ Hệ Thống)

1. **Max Iterations**: Giới hạn số lần lặp (mặc định: 6)
2. **Timeout**: Giới hạn thời gian mỗi LLM call (mặc định: 60s)
3. **Error Handling**: Bắt lỗi và ghi vào `state.errors`
4. **Validation**: Pydantic schemas cho tất cả input/output

---

## 📦 Deliverables (Bài Nộp)

| STT | Yêu Cầu | Mô Tả |
|-----|---------|--------|
| 1 | GitHub Repo | Code hoàn chỉnh |
| 2 | Trace Screenshot | Ảnh chụp workflow execution |
| 3 | Benchmark Report | So sánh single vs multi-agent |
| 4 | Giải thích | Failure modes và cách fix |

---

## 🔗 Tài Liệu Tham Khảo

- [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- [LangGraph Concepts](https://langchain-ai.github.io/langgraph/concepts/)
- [LangSmith Tracing](https://docs.smith.langchain.com/)

---

*Lưu ý: Đảm bảo đã kích hoạt `.venv` trước khi chạy các lệnh!*
