"""Generate 【正式版】会议/活动筹备模板 .docx from events.json.
Uses named-placeholder template and replaces {{placeholder}} with data.
"""
import json
import os
import shutil
import zipfile
import io
from lxml import etree

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "events.json")
TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), "template.docx")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

NSMAP = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def make_val(value):
    if value is None:
        return ""
    s = str(value).strip()
    return s


def build_placeholder_map(event):
    """Build a dict of {{name}} → value for all placeholders in the template."""
    s1 = event.get("section1_basic_info", {})
    s2 = event.get("section2_schedule", {})
    s3 = event.get("section3_preparation", {})
    s4 = event.get("section4_departure", {})
    s5 = event.get("section5_wrapup", {})

    attr = s1.get("会议属性", {}) or {}
    vips = s2.get("要员简介", []) or []
    schedule = s2.get("日程", []) or []
    todos = s3.get("待办", []) or []
    hotel = s4.get("酒店安排", {}) or {}

    # Build schedule text
    schedule_text_parts = []
    for item in schedule:
        date_str = item.get("日期", "")
        entries = item.get("条目", [])
        day_text = f"【{date_str}】\n"
        for e in entries:
            day_text += f"  {e.get('时间', '')}  {e.get('内容', '')}\n"
        schedule_text_parts.append(day_text.strip())
    schedule_text = "\n".join(schedule_text_parts)

    # Build VIP text for 要员简介
    vip_summary_parts = []
    for v in vips:
        name = v.get("姓名", "")
        title = v.get("Title公司", "")
        summary = v.get("简介近期动态", "")
        vip_summary_parts.append(f"{name}\n{title}\n{summary}")
    vip_summary = "\n\n".join(vip_summary_parts)

    # First VIP details
    vip1_name = vips[0].get("姓名") if len(vips) > 0 else ""
    vip1_title = vips[0].get("Title公司") if len(vips) > 0 else ""
    vip1_summary = vips[0].get("简介近期动态") if len(vips) > 0 else ""

    return {
        # Section 1
        "会议名称": make_val(s1.get("会议名称")),
        "会议时间": make_val(s1.get("会议时间")),
        "会议地点": make_val(s1.get("会议地点")),
        "会议受众": make_val(s1.get("会议受众")),
        "会议规模": make_val(s1.get("会议规模")),
        "主办方资质": make_val(s1.get("主办方资质")),
        "会议背景": make_val(s1.get("会议背景")),
        "会议预期": make_val(s1.get("会议预期")),
        "参会要员": make_val(s1.get("参会要员")),
        # Section 2
        "日程": schedule_text or "xxxx",
        "要员简介": vip_summary or "xxxx",
        "要员1姓名": vip1_name or "xxxx",
        "要员1Title公司": vip1_title or "xxxx",
        "要员1简介近期动态": vip1_summary or "xxxx",
        # Section 3
        "演讲时长": make_val(s3.get("演讲时长")),
        "演讲时间": make_val(s3.get("演讲时间")),
        "待办1": make_val(todos[0] if len(todos) > 0 else ""),
        "待办2": make_val(todos[1] if len(todos) > 1 else ""),
        "参考资料": make_val(s3.get("参考资料")),
        "分享主题": make_val(s3.get("分享主题")),
        "内容梗概": make_val(s3.get("内容梗概")),
        # Section 4
        "大交通安排": make_val(s4.get("大交通安排")),
        "去程": make_val(s4.get("去程")),
        "回程": make_val(s4.get("回程")),
        "酒店安排说明": make_val(s4.get("酒店安排说明")),
        "酒店名称": make_val(hotel.get("名称")),
        "酒店地址": make_val(hotel.get("地址")),
        "酒店确认号": make_val(hotel.get("确认号")),
        "目的地天气": make_val(s4.get("目的地天气")),
        "出行提示": make_val(s4.get("出行提示")),
        # Section 5
        "照片存档": make_val(s5.get("照片存档")),
        "录像存档": make_val(s5.get("录像存档")),
        "发言稿完整版": make_val(s5.get("发言稿完整版")),
        "发言稿整理版": make_val(s5.get("发言稿整理版")),
        "活动宣传发布内容": make_val(s5.get("活动宣传发布内容")),
        "主办方是否索取文档分享版": make_val(s5.get("主办方是否索取文档分享版")),
    }


def apply_checkmarks(root, event):
    """Add ☑ before selected options in 会议属性 and other checkbox-style fields."""

    s1 = event.get("section1_basic_info", {})
    attr = s1.get("会议属性", {})

    selected_texts = set()
    for category, options in attr.items():
        if isinstance(options, dict):
            for opt_text, checked in options.items():
                if checked:
                    selected_texts.add(opt_text)
        elif isinstance(options, str) and options.strip():
            for item in options.split(","):
                item = item.strip()
                if item:
                    selected_texts.add(item)

    if not selected_texts:
        return

    all_t = root.findall(".//w:t", NSMAP)
    for el in all_t:
        text = el.text or ""
        if text in selected_texts:
            el.text = "☑ " + text


def generate_docx(event, output_path):
    """Generate a docx by replacing {{placeholder}} placeholders in the template."""

    shutil.copy2(TEMPLATE_FILE, output_path)

    with zipfile.ZipFile(output_path, "r") as z:
        doc_xml = z.read("word/document.xml")

    root = etree.fromstring(doc_xml)

    placeholder_map = build_placeholder_map(event)

    # Replace all {{name}} placeholders (handles Word-split runs)
    for para in root.findall(".//{%s}p" % NSMAP["w"]):
        t_elements = para.findall(".//{%s}t" % NSMAP["w"])
        if not t_elements:
            continue
        combined = "".join(el.text or "" for el in t_elements)
        if "{{" not in combined or "}}" not in combined:
            continue
        for name, value in placeholder_map.items():
            placeholder = "{{" + name + "}}"
            if placeholder in combined:
                combined = combined.replace(placeholder, value if value else "xxxx")
        t_elements[0].text = combined
        for el in t_elements[1:]:
            el.text = ""

    # Apply checkmarks
    apply_checkmarks(root, event)

    new_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    buf = io.BytesIO()
    with zipfile.ZipFile(output_path, "r") as zin:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
    buf.seek(0)

    with open(output_path, "wb") as f:
        f.write(buf.getvalue())


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = data.get("events", [])
    if not events:
        print("No events found")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for event in events:
        eid = event.get("id", "unknown")
        name = event.get("name", eid)
        output_path = os.path.join(OUTPUT_DIR, f"{eid}.docx")
        generate_docx(event, output_path)
        print(f"Generated: {output_path} ({name})")


if __name__ == "__main__":
    main()
