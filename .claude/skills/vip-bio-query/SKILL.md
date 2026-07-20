---
name: vip-bio-query
description: Use when the user asks to look up a VIP's bio and recent activities — searches the web for the person by name + title/company, summarizes into 个人简介 and 近期动态 sections (~300 chars each), updates events.json, and pushes to GitHub
---

# VIP Bio Query

Search the web for a person's bio and recent activities, then update `data/events.json` for a specific event's 要员简介 entry.

## When to Use

User mentions refreshing/querying a VIP's bio. Two trigger forms:

**Simple form (preferred by user):**
- 「刷新 [name] 简介」 (e.g. 「刷新周鸿祎简介」) — finds the VIP by name across ALL events and updates every matching entry

**Explicit form (when precision needed):**
- 「刷新要员简介 [event-id] [name] [title]」
- 「刷新 XX 活动 [name] 的简介」

Required inputs: VIP name (always). Title/company is optional but helpful — if the form provides it, include it in search queries. If user uses the simple form, scan ALL events for matches.

NOT for: searching for non-VIP entities (companies, products).

## Workflow

1. **Parse input**: extract event-id, name, title.
2. **Read events.json**: located at `data/events.json` in the project root. Parse the JSON.
3. **Find event**: locate the event in `events` array where `event.id === event-id`.
4. **Find VIP**: in `event.section2_schedule.要员简介`, find the entry where `姓名 === name` (also try partial match if exact match fails). If not found, ask user to add the VIP first via the form.
5. **Web search**: use the WebSearch tool with queries like:
   - `[name] [title] 简介` (Chinese bio search)
   - `[name] [title] 个人背景` (background search)
   - `[name] [title] 近期` (recent activities)
   - `[name] [title] 2024 OR 2025 OR 2026` (recent year filter)
6. **Summarize** into two sections per the Output Template.
7. **Update events.json**: set `VIP.简介近期动态` to the summarized text (multi-line string).
8. **Push to GitHub**: from project root, run `git add data/events.json && git commit -m "Update VIP bio: [name]" && git pull github master --no-rebase --no-edit && git push github master`.

## Output Template

The `简介近期动态` field should contain EXACTLY this format (plain text with line breaks, no markdown):

```
个人简介：
- [bullet 1: current role and primary affiliation]
- [bullet 2: career history — previous positions, notable employers]
- [bullet 3: education, awards, or notable achievements]
近期动态：
- [bullet 1: most recent news/announcement within the last 1-3 years]
- [bullet 2: recent speeches, projects, publications, or appearances]
- [bullet 3: any other notable recent activity, or "无其他公开动态" if none]
```

**Length**: Each section should be around 300 Chinese characters total (across all bullets). Aim for 3-5 bullets per section.

**Missing info rules:**
- If NO reliable info found for 个人简介: replace all 个人简介 bullets with a single line: `- 网上信息源不足`
- If NO reliable info found for 近期动态: replace all 近期动态 bullets with a single line: `- 网上信息源不足`
- If NOTHING is found at all (person is unverifiable): set the entire field to:
  ```
  个人简介：
  - 网上信息源不足
  近期动态：
  - 网上信息源不足
  ```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Adding "Here is the result" preamble | Output goes directly into the JSON field, no chat preamble |
| Using markdown `**bold**` or `### headers` | Plain text only — `个人简介：` and `近期动态：` are plain lines |
| Writing only one bullet per section | Aim for 3-5 bullets unless info is genuinely scarce |
| Fabricating details when search returns nothing | Use `- 网上信息源不足` instead of guessing |
| Skipping the git push step | User needs to refresh the form to see the update — must push to GitHub |
| Forgetting to find the right VIP by name | Match `姓名` field; if multiple similar names, confirm with user |
| Including source URLs in the field | Just the summarized bullets, no URLs |

## Red Flags

If you find yourself doing any of these, STOP and re-read the rules:
- Adding "Based on the search results..." or "Sources:" to the JSON field
- Using markdown formatting (`**`, `###`, `[](...)`) inside the field value
- Skipping the push to GitHub (user won't see the update otherwise)
- Writing more or less than 2 sections (个人简介 + 近期动态)
- Fabricating bio details instead of using "网上信息源不足"

## Example Field Value

For input: event-id=`qianyuan-review-20260710`, name=`张三`, title=`微软亚洲研究院院长`

The `简介近期动态` field should end up containing:

```
个人简介：
- 现任微软亚洲研究院院长，负责基础科学研究方向
- 加入微软前在卡内基梅隆大学获得博士学位，师从X教授
- 2018年起担任现职，主导多项AI基础研究项目
近期动态：
- 2024年发表GPT相关论文，提出新的预训练范式
- 在2024年NeurIPS大会上做主题演讲
- 近期主导微软与清华大学的联合AI实验室项目
```