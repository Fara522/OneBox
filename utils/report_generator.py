from utils.helpers import format_duration, format_datetime


def build_report_text(report: dict) -> str:
    status_text = "✅ Tugatildi" if report.get("status") == "completed" else "🔄 Jarayonda"
    assistant = report.get("assistant_name") or "—"
    end_str = format_datetime(report.get("end_time")) if report.get("end_time") else "—"
    duration_str = format_duration(report["duration_minutes"]) if report.get("duration_minutes") else "—"

    return (
        "──────────────\n"
        "🧾 ISH HISOBOTI\n"
        "──────────────\n\n"
        f"🏭 Stanok: {report['machine_name']}\n\n"
        f"🙎🏻‍♂️ Ishchi: {report['worker_name']}\n"
        f"🙎🏻‍♂️ Yordamchi: {assistant}\n\n"
        f"📦 Mahsulot:\n{report['product_name']}\n\n"
        f"🔢 Soni:\n{report['quantity']:,} ta\n\n"
        f"🕐 Boshlanish:\n{format_datetime(report['start_time'])}\n\n"
        f"🕐 Tugash:\n{end_str}\n\n"
        f"⏳ Ish vaqti:\n{duration_str}\n\n"
        f"✅ Status:\n{status_text}\n"
        "──────────────"
    )


def build_stats_text(data: dict) -> str:
    s = data["summary"]
    total = int(s["total_reports"] or 0)
    qty = int(s["total_quantity"] or 0)
    avg_min = int(s["avg_duration"] or 0)
    total_min = int(s["total_minutes"] or 0)

    lines = [
        f"📊 {data['label']} statistika\n",
        f"📋 Jami hisobotlar: {total}",
        f"📦 Jami mahsulot: {qty:,} ta",
        f"⏱ O'rtacha vaqt: {format_duration(avg_min)}",
        f"⏳ Umumiy vaqt: {format_duration(total_min)}",
    ]

    if data["by_worker"]:
        lines.append("\n👷 Ishchilar bo'yicha:")
        for row in data["by_worker"]:
            lines.append(f"  • {row['full_name']}: {int(row['qty'] or 0):,} ta ({row['cnt']} ish)")

    if data["by_machine"]:
        lines.append("\n🏭 Stanoklar bo'yicha:")
        for row in data["by_machine"]:
            lines.append(f"  • {row['name']}: {int(row['qty'] or 0):,} ta ({row['cnt']} ish)")

    return "\n".join(lines)
