import os
import re
import time
import json
import pathlib
import typing as t
import requests


class FinancialReportCrawler:
    """巨潮资讯财报爬虫：抓取并下载 PDF 文件

    使用 POST http://www.cninfo.com.cn/new/hisAnnouncement/query 获取公告列表，
    从返回 JSON 的 announcements 中提取 adjunctUrl 拼接为 PDF 下载地址。
    """

    def __init__(self, download_root: t.Optional[str] = None) -> None:
        self.base_url = "http://www.cninfo.com.cn"
        self.session = requests.Session()
        self.set_headers()
        self._stock_index: dict[str, str] = {}
        self.download_root = download_root or str(pathlib.Path("data/reports").resolve())
        os.makedirs(self.download_root, exist_ok=True)

    def set_headers(self) -> None:
        self.session.headers.update({
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/new/commonUrl/pageOfSearch?url=disclosure/list/search",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        })

    # -------- 公共工具 ---------
    def _load_stock_index(self) -> None:
        """加载 code -> orgId 映射，覆盖深/沪两市。
        参考公开 JSON：szse_stock.json / sse_stock.json。
        若某一端点不可用，跳过不致命。
        """
        endpoints = [
            f"{self.base_url}/new/data/szse_stock.json",
            f"{self.base_url}/new/data/sse_stock.json",
        ]
        for url in endpoints:
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                for it in data.get("stockList", []):
                    code = it.get("code")
                    org = it.get("orgId")
                    if code and org:
                        self._stock_index[code] = org
            except Exception:
                # 某端点不可用时忽略
                continue

    def _resolve_stock_pair(self, stock_code: str) -> tuple[str, str, str]:
        """返回 (<code>, <orgId>, <column>)。
        - column: 深交所用 'szse'，沪交所用 'sse'（按代码前缀粗略判断）
        """
        if not self._stock_index:
            self._load_stock_index()
        org = self._stock_index.get(stock_code)
        # 粗略按代码前缀确定 column
        column = "szse" if stock_code.startswith(("0", "2", "3")) else "sse"
        if not org:
            # 未命中索引时提示用户补充 orgId（也允许后续直接传入硬编码映射）
            raise KeyError(f"未找到 {stock_code} 的 orgId，请补充映射或检查代码是否正确。")
        return stock_code, org, column

    @staticmethod
    def _category_code(report_type: str) -> str:
        """映射报告类型到巨潮 category 代码。
        年报/半年报先覆盖，其他类型后续补充。
        """
        mapper = {
            "annual": "category_ndbg_szsh",
            "semi": "category_bndbg_szsh",
        }
        rt = (report_type or "").lower()
        if rt not in mapper:
            raise ValueError(f"不支持的 report_type: {report_type}. 可选: annual, semi")
        return mapper[rt]

    # -------- 接口调用 ---------
    def _query_page(self, stock_pair: str, column: str, category: str, se_date: str, page_num: int) -> dict:
        payload = {
            "pageNum": page_num,
            "pageSize": 30,
            "tabName": "fulltext",
            "column": column,
            "plate": "",
            "stock": stock_pair,
            "searchkey": "",
            "secid": "",
            "category": category,
            "trade": "",
            "seDate": se_date,
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }
        resp = self.session.post(f"{self.base_url}/new/hisAnnouncement/query", data=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _iter_announcements(self, stock_code: str, year: int, report_type: str, org_id: t.Optional[str] = None, column_override: t.Optional[str] = None) -> t.Iterable[dict]:
        if org_id is not None:
            code = stock_code
            org = org_id
            column = column_override or ("szse" if stock_code.startswith(("0", "2", "3")) else "sse")
        else:
            code, org, column = self._resolve_stock_pair(stock_code)
        stock_pair = f"{code},{org}"
        se_date = f"{year}-01-01~{year}-12-31"
        category = self._category_code(report_type)
        page = 1
        while True:
            data = self._query_page(stock_pair, column, category, se_date, page)
            items = data.get("announcements", []) or []
            if not items:
                break
            for it in items:
                yield it
            # 简单翻页：若返回条数不足 pageSize 则终止
            if len(items) < 30:
                break
            page += 1
            time.sleep(0.8)  # 速率限制，避免触发风控

    # -------- 下载 PDF ---------
    @staticmethod
    def _safe_name(name: str) -> str:
        return re.sub(r"[\\/:*?\"<>|]", "-", name).strip()

    @staticmethod
    def _build_pdf_url(adjunct_url: str) -> str:
        # 常见前缀为 static.cninfo.com.cn
        if adjunct_url.startswith("http"):
            return adjunct_url
        return f"http://static.cninfo.com.cn/{adjunct_url.lstrip('/') }"

    def _download_pdf(self, url: str, save_path: str) -> None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with self.session.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

    # -------- 对外主流程 ---------
    async def crawl_report(self, stock_code: str, year: int, report_type: str, org_id: t.Optional[str] = None, column: t.Optional[str] = None) -> dict:
        """核心爬取方法：抓取指定股票、年份、类型的 PDF 并保存。
        返回结果包含计数与保存目录。
        """
        saved = 0
        base_dir = os.path.join(self.download_root, stock_code, str(year), report_type)
        os.makedirs(base_dir, exist_ok=True)
        for ann in self._iter_announcements(stock_code, year, report_type, org_id=org_id, column_override=column):
            title = ann.get("announcementTitle", "")
            # 过滤摘要/英文版等非主体
            if re.search("摘要", title) or re.search("英文", title):
                continue
            adjunct = ann.get("adjunctUrl")
            if not adjunct:
                continue
            pdf_url = self._build_pdf_url(adjunct)
            # 文件名：代码_公司_标题_公告ID.pdf
            sec_code = ann.get("secCode", stock_code)
            sec_name = (ann.get("secName", "") or "").replace("*", "")
            ann_id = ann.get("announcementId", "")
            fname = self._safe_name(f"{sec_code}_{sec_name}_{title}_{ann_id}.pdf")
            save_path = os.path.join(base_dir, fname)
            try:
                self._download_pdf(pdf_url, save_path)
                saved += 1
                time.sleep(0.6)  # 速率限制
            except Exception:
                # 单个失败不影响整体
                continue
        return {"downloaded": saved, "save_dir": base_dir}


if __name__ == "__main__":
    # 便于直接试跑：示例抓取 600519 2023 年年报
    crawler = FinancialReportCrawler()
    try:
        # 同步地调用异步方法（仅示例），实际可在 FastAPI/async 环境中 await
        import asyncio
        res = asyncio.run(crawler.crawl_report("600519", 2023, "annual"))
        print("result:", json.dumps(res, ensure_ascii=False))
    except Exception as e:
        print("error:", e)