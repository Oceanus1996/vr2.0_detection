import openai
import pandas as pd
import json
from tqdm import tqdm
from string import Template
# ✅ OpenAI API 初始化
openai.api_key = f"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"   # ← 请替换
MODEL = "gpt-4o"             # 可改为 gpt-4o 或 gpt-5



def chat_read_bug_report(filepath= r"D:\vr_detection_2.0\pythonProject\filter_new90.csv"):
    # ✅ 读取 Excel
    df = pd.read_csv(filepath)  # 文件需含 'text' 或 'bug_report' 列
    if "text" not in df.columns:
        df.rename(columns={df.columns[0]: "text"}, inplace=True)

    # ✅ 仅保留 predicted_label == 1 的行（可复现的）
    if "predicted_label" in df.columns:
        df = df[df["predicted_label"] == 1].reset_index(drop=True)
        print(f"📊 已筛选可复现样本: {len(df)} 条")
    else:
        print("⚠️ 未检测到 predicted_label 列，将处理全部数据。")

    # ✅ Prompt 模板（中英双语）
    PROMPT_TEMPLATE = Template("""
    请从以下 bug report 中提取：
    1. 一组交互三元组 (action, target, context_or_condition, effect_or_observation)
    2. 用一句自然语言总结 bug 的核心含义。

    返回 JSON，格式如下：
    {
      "triples": [
        {
          "action": "...",
          "target": "...",
          "context_or_condition": "...",
          "effect_or_observation": "..."
        }
      ],
      "summary": "一句话总结"
    }
    Bug report:
    \"\"\"$text\"\"\"
    """)

    # ✅ 定义调用函数
    def analyze_report(text):
        prompt = PROMPT_TEMPLATE.substitute(text=text.strip())
        try:
            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            result = response["choices"][0]["message"]["content"].strip()
            try:
                return json.loads(result)
            except:
                return {"triples": [], "summary": result}
        except Exception as e:
            return {"triples": [], "summary": f"Error: {e}"}

    # ✅ 批量处理（每 50 条）
    batch_size = 50
    all_results = []

    for start in range(0, len(df), batch_size):
        end = start + batch_size
        batch_df = df.iloc[start:end]
        print(f"🔹 Processing {start+1}-{min(end, len(df))} ...")

        for i, row in tqdm(batch_df.iterrows(), total=len(batch_df)):
            text = row["text"]
            repo = row.get("repo", "")
            typ = row.get("type", "")
            bug_id = row.get("id", "")
            author = row.get("author", "")
            label = row.get("predicted_label","")
            index = i
            result = analyze_report(text)
            all_results.append({
                "repo": repo,
                "type": typ,
                "id": bug_id,
                "author": author,
                "text": text,
                "index": index,
                "predicted_label": result.get("predicted_label", ""),
                "reproducible_prob": result.get("reproducible_prob", None),
                "triples": result.get("triples", []),
                "summary": result.get("summary", "")
            })

    # ✅ 保存到 JSON 文件
    with open("bug_reports_analysis.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print("✅ All done! Results saved to 'bug_reports_analysis.json'")


if __name__ == "__main__":
    chat_read_bug_report()