import asyncio
from pathlib import Path
from radar_core import DEFAULT_CONFIG, deep_copy_jsonable, load_json, save_json, run_scan, export_csv, create_one_page_pdf, create_one_page_html, update_seen

async def main():
    config = load_json("radar_config.json", deep_copy_jsonable(DEFAULT_CONFIG))
    result = await run_scan(config, include_seen=False, seen_path="seen_items.json")
    d = result["run_date"]
    save_json({k:v for k,v in result.items() if k != "seen_state"}, f"radar_results_{d}.json")
    export_csv(result["items"], f"radar_results_{d}.csv")
    create_one_page_pdf(result["items"], f"geospatial_radar_{d}.pdf", d, config.get("max_report_items",7))
    create_one_page_html(result["items"], f"geospatial_radar_{d}.html", d, config.get("max_report_items",7))
    update_seen(result["items"], result["seen_state"], "seen_items.json")
    print(f"Created geospatial_radar_{d}.pdf with {min(len(result['items']), config.get('max_report_items',7))} items")

if __name__ == "__main__":
    asyncio.run(main())
