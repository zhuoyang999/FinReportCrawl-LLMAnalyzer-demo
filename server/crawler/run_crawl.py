import argparse
import json
import asyncio
from financial_report_crawler import FinancialReportCrawler


def main():
    parser = argparse.ArgumentParser(description="Crawl CNINFO financial reports and download PDFs")
    parser.add_argument("code", help="股票代码，如 600519 或 000001")
    parser.add_argument("year", type=int, help="报告年份，如 2023")
    parser.add_argument("type", choices=["annual", "semi"], help="报告类型：annual 或 semi")
    parser.add_argument("--out", dest="out", default=None, help="自定义下载根目录，可选")
    parser.add_argument("--orgid", dest="orgid", default=None, help="可选：指定 orgId 以绕过索引")
    parser.add_argument("--column", dest="column", choices=["szse", "sse"], default=None, help="可选：指定交易所列，默认按代码推断")
    args = parser.parse_args()

    crawler = FinancialReportCrawler(download_root=args.out)
    res = asyncio.run(crawler.crawl_report(args.code, args.year, args.type, org_id=args.orgid, column=args.column))
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()