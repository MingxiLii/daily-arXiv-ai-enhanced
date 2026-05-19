# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import arxiv
import json
import os
import re
import sys
from datetime import datetime, timedelta

from scrapy.exceptions import DropItem


# 电池材料 + AI4Science 关键词过滤
# Battery materials + AI4Science keyword filtering
KEYWORDS = [
    # 电池相关 / Battery related
    r"\bbatter(y|ies)\b",
    r"\blithium\b",
    r"\belectrolyte\b",
    r"\bcathode\b",
    r"\banode\b",
    r"\belectrode\b",
    r"\bsolid.state\b",
    r"\benergy storage\b",
    r"\belectrochem",
    r"\bion transport\b",
    r"\bion conduct",
    r"\bintercalat",
    r"\bsodium.ion\b",
    r"\bpotassium.ion\b",
    r"\bcharge.discharge\b",
    r"\bcycl(ing|ability)\b",
    r"\bcoulombic\b",
    r"\bsupercapacitor\b",
    r"\bfuel cell\b",
    # 材料科学 + AI 交叉 / Materials science + AI intersection
    r"\bmaterials? discover",
    r"\bmaterials? design\b",
    r"\bmaterials? screen",
    r"\bmaterials? informatics\b",
    r"\bmaterials? generat",
    r"\bcrystal structure predict",
    r"\batomistic simulat",
    r"\bmolecular dynamics\b",
    r"\bdensity functional\b",
    r"\bfirst.principles?\b",
    r"\bmachine.learn\w*\s+potent",
    r"\bforce field\b",
    r"\binteratomic potential\b",
    r"\bgraph neural network\b",
    r"\bequivariant\b",
    r"\bfoundation model\b",
    r"\blarge language model\b",
    r"\bllm\b",
    r"\bai.?(for|driven|guided|assisted|accelerat)",
    r"\bactive learning\b",
    r"\bbayesian optimiz",
    r"\bhigh.throughput screen",
    r"\binverse design\b",
]

# 预编译正则表达式 / Pre-compile regex patterns
KEYWORD_PATTERNS = [re.compile(kw, re.IGNORECASE) for kw in KEYWORDS]


class KeywordFilterPipeline:
    """过滤论文：只保留标题或摘要中包含相关关键词的论文。
    Filter papers: only keep those with relevant keywords in title or abstract."""

    def process_item(self, item: dict, spider):
        text = f"{item.get('title', '')} {item.get('summary', '')}"
        for pattern in KEYWORD_PATTERNS:
            if pattern.search(text):
                return item
        raise DropItem(f"No matching keywords: {item.get('title', '')[:80]}")


class DailyArxivPipeline:
    def __init__(self):
        self.page_size = 100
        self.client = arxiv.Client(self.page_size)

    def process_item(self, item: dict, spider):
        item["pdf"] = f"https://arxiv.org/pdf/{item['id']}"
        item["abs"] = f"https://arxiv.org/abs/{item['id']}"
        search = arxiv.Search(
            id_list=[item["id"]],
        )
        paper = next(self.client.results(search))
        item["authors"] = [a.name for a in paper.authors]
        item["title"] = paper.title
        item["categories"] = paper.categories
        item["comment"] = paper.comment
        item["summary"] = paper.summary
        return item