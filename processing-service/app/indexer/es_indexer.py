# app/indexer/es_indexer.py
from elasticsearch import AsyncElasticsearch

class ESIndexer:
    def __init__(self):
        self.client = AsyncElasticsearch(hosts=["http://localhost:9200"])

    async def index(self, log: dict):
        await self.client.index(index="logs", document=log)