---
name: travel-weather-query
description: Use when the user asks about weather or traffic for a Chinese city on a specific date — queries weather conditions and traffic restrictions, then outputs two lines of plain text
---

# Travel Weather Query

Query weather and traffic info for a Chinese city on a specific date. Output exactly two lines of plain text — nothing more, nothing less.

## When to Use

User mentions: weather, temperature, 天气, 限行, 限号, traffic restrictions for a Chinese city with a date.

NOT for: international cities, general travel advice, date ranges, non-Chinese locations.

## Core Rules

**Scope:** Chinese cities only. Date must be today or a specific future date (user must provide the date).

**Weather limit:** Weather query covers current day to 7 days out only. If date is beyond 7 days, state "暂无预报数据" for all weather fields.

## Data Sources (strict — do NOT use other sources)

| Data | Source |
|------|--------|
| Weather | `weather.com.cn` (中国天气网) |
| Traffic — Priority 1 | `[city] 交管局` website |
| Traffic — Priority 2 | Baidu Maps (百度地图) |

**CRITICAL:** If the approved source returns no results, use the fallback markers ("暂无" / "暂无信息"). Never switch to unapproved sources. Do NOT use: yzqxj.com, accuweather.com, bendibao.com, eastday.com, 163.com, nmc.cn, toutiao.com, or any other weather/traffic source.

## Workflow

1. Parse input: extract city name and date. If date is relative ("明天", "后天"), compute the absolute date (YYYY年M月D日).
2. Verify: city is Chinese, date is today or future, date within 7 days for weather.
3. Search weather: `site:weather.com.cn [city] 天气 [date]`
4. Search traffic: first `[city] 交管局 限行 [date]`, then if needed `百度 [city] 限行尾号 [date]`
5. Assemble output using the template below.

## Output Template

Your ENTIRE response must be exactly these two lines. No preamble, no "Here is the result", no source list, no markdown, no extra blank lines.

```
[城市][日期]天气：[天气情况]，温度[XX]°C ~ [XX]°C，风力[X]级，降水概率[XX]%，建议穿着[穿衣类型]。
交通提示：限行尾号[XX]，重大活动[XX]，临时管制[XX]。
```

**Field rules:**
- Weather line: start with `[城市][日期]天气：` and include all 5 fields separated by `，`.
- Traffic line: start with `交通提示：` and include all 3 fields separated by `，`.
- Missing weather field (within 7-day range): use "暂无".
- Missing traffic field: use "暂无信息".
- Beyond 7 days: entire weather line becomes `[城市][日期]天气：暂无预报数据。` (do NOT attach units like °C/级/% to the fallback text). Traffic line still uses "暂无信息" for each field.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using wrong weather source (accuweather, nmc.cn) | Use ONLY weather.com.cn |
| Using wrong traffic source (bendibao, toutiao.com) | Use ONLY 交管局 or 百度地图 |
| Switching sources when approved ones return no results | Use "暂无" / "暂无信息" instead |
| Adding "Here is the result" or source links outside template | Two lines only — nothing before, nothing after |
| Adding markdown (bold, bullets, code blocks) | Plain text only |
| "降水概率较高" without percentage | Find specific percentage, or use "暂无" |
| Not checking 7-day limit | Weather beyond 7 days → "暂无预报数据" |
| Beyond 7 days: "暂无预报数据°C" with units | Remove units — just "暂无预报数据" |
| "限行尾号暂无" (mixing weather/traffic markers) | Weather fields → "暂无", traffic fields → "暂无信息" |

## Red Flags

If you find yourself writing any of these, STOP and re-read the template rules:
- "Based on the search results..."
- "Here is the result..."
- "Sources:" or source URLs
- Any markdown formatting (**bold**, - bullets)
- Any weather/traffic source URL that is NOT weather.com.cn, a 交管局 site, or baidu.com
- More than 2 lines of output
