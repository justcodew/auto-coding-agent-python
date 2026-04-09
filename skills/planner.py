import config
from core.llm_client import llm_client
from core.state_manager import StateManager
from core.file_utils import parse_meta_from_response, save_file, save_meta, read_file

def run_planner():
    """执行 Planner Skill"""
    print("\n📋 [Planner] 开始制定开发计划...")
    
    # 读取输入
    task = StateManager.get_current_task()
    architecture_file = config.PROJECT_ROOT / "architecture.md"
    architecture_content = read_file(architecture_file) if architecture_file.exists() else ""
    
    # 构建 Prompt
    prompt = f"""[角色]
你是一位资深技术项目经理和系统架构师 (Planner)。你的唯一职责是根据给定的任务需求，制定一份精确、无歧义的开发计划。

[全局上下文]
请仔细阅读以下项目架构文档，你的计划必须符合其约束：
--- 架构文档 ---
{architecture_content if architecture_content else "无特殊架构约束"}
--- 架构文档结束 ---

[任务输入]
当前任务描述如下：
--- 任务描述 ---
{task.get('description', '')}
--- 任务描述结束 ---

[输出要求]
请严格按照以下两部分结构输出，不要添加任何额外说明。

第一部分：开发计划 (保存为 plans/plan_v1.md)
请用 Markdown 格式撰写一份详细的开发计划，必须包含：
1. **任务理解**：用一句话总结你对任务的核心目标的理解。
2. **技术方案**：描述具体的实现路径、涉及的算法或库。
3. **文件变更清单**：列出所有需要新增、修改或删除的文件及其路径。
4. **实现步骤**：一个有序的、可独立验证的步骤列表。

第二部分：计划元数据 (保存为 plans/plan_v1.meta.json)
请将你对计划的思考过程总结为 JSON 格式，并用 `[META_START]` 和 `[META_END]` 标记包裹。

[META_START]
{{
  "agent": "Planner",
  "key_interpretation": "用一句话概括你对任务核心需求的理解。",
  "assumptions": [
    "列出你在制定计划时做出的所有关键假设。"
  ],
  "potential_risks": [
    "指出执行此计划可能遇到的技术难点或风险。"
  ],
  "next_step_hint": "给负责编码的 Coder 的一句关键提示，例如需要特别注意的性能点或边界条件。"
}}
[META_END]"""
    
    # 调用 LLM
    response = llm_client.chat(prompt)
    
    # 解析响应
    main_content, meta = parse_meta_from_response(response)
    
    # 保存文件
    plan_path = config.WORKSPACE_DIR / "plans" / "plan_v1.md"
    save_file(plan_path, main_content)
    if meta:
        save_meta(meta, plan_path)
    
    # 更新状态
    StateManager.update(current_phase="coding", retry_count=0)
    StateManager.append_decision_trail({
        "agent": "Planner",
        "output_file": str(plan_path),
        "key_interpretation": meta.get("key_interpretation", "") if meta else ""
    })
    
    print(f"✅ [Planner] 计划已保存至 {plan_path}")
    return main_content