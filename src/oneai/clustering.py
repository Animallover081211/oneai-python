from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import List
import requests
import oneai


base_url = "https://staging.oneai.com/clustering/v1/collections"

def _get_req(path: str, api_key: str = None):
    api_key = api_key or oneai.api_key
    if not api_key:
        raise Exception("API key is required")
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }
    response = requests.get(f"{base_url}/{path}", headers=headers)
    return json.loads(response.content)

def _post_req(path: str, data: dict, api_key: str = None):
    api_key = api_key or oneai.api_key
    if not api_key:
        raise Exception("API key is required")
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }
    response = requests.post(f"{base_url}/{path}", headers=headers, json=data)
    return json.loads(response.content)


def fetch_collections(api_key: str = None):
    return [Collection(name) for name in _get_req("", api_key)]


@dataclass
class Item:
    id: int
    text: str
    created_at: datetime
    distance: float
    phrase: "Phrase" = field(repr=False)
    cluster: "Cluster" = field(repr=False)

    @classmethod
    def from_dict(cls, phrase: "Phrase", object: dict) -> "Item":
        return cls(
            id=object["id"],
            text=object["original_text"],
            created_at=datetime.strptime(
                object["create_date"], f"%Y-%m-%d %H:%M:%S.%f"
            ),
            distance=object["distance_to_phrase"],
            phrase=phrase,
            cluster=phrase.cluster,
        )


@dataclass
class Phrase:
    id: int
    text: str
    item_count: int
    cluster: "Cluster" = field(repr=False)
    collection: "Collection" = field(repr=False)

    @property
    def items(self) -> List[Item]:
        url = f"phrases/{self.id}/items"
        return [Item.from_dict(self, item) for item in _get_req(url, self.collection.api_key)]

    @classmethod
    def from_dict(cls, cluster: "Cluster", object: dict) -> "Phrase":
        return cls(
            id=object["phrase_id"],
            text=object["text"],
            item_count=object["items_count"],
            cluster=cluster,
            collection=cluster.collection,
        )


@dataclass
class Cluster:
    id: int
    text: str
    phrase_count: int
    metadata: str
    collection: "Collection" = field(repr=False)
    _phrases: List[Phrase] = field(default_factory=list, repr=False)

    @property
    def phrases(self) -> List[Phrase]:
        # refetch? cache?
        return self._phrases

    def add_items(self, *items: str):
        url = f"{self.collection.name}/items"
        data = [
            {
                "text": item,
                "force-cluster-id": self.id,
            }
            for item in items
        ]
        _post_req(url, data, self.collection.api_key)

    @classmethod
    def from_dict(cls, collection: "Collection", object: dict) -> "Cluster":
        cluster = cls(
            id=object["cluster_id"],
            text=object["cluster_phrase"],
            phrase_count=object["phrases_count"],
            metadata=object["metadata"],
            collection=collection,
        )
        cluster._phrases = [
            Phrase.from_dict(cluster, phrase) for phrase in object["phrases"]
        ]
        return cluster


class Collection:
    def __init__(self, name: str, api_key: str = None):
        self.name = name
        self.api_key = api_key or oneai.api_key

    @property
    def clusters(self) -> List[Cluster]:
        # generator w pagination? caching?
        url = f"{self.name}/clusters"
        return [
            Cluster.from_dict(self, cluster) for cluster in _get_req(url, self.api_key)
        ]

    @property
    def find(self) -> List[Cluster]:
        url = f"{self.name}/clusters/find"
        return [
            Cluster.from_dict(self, cluster) for cluster in _get_req(url, self.api_key)
        ]

    def add_items(self, *items: str, force_new_cluster: bool = False):
        url = f"{self.name}/items"
        data = [
            {
                "text": item,
                "force-new-cluster": force_new_cluster,
            }
            for item in items
        ]
        _post_req(url, data, self.api_key)

    def __repr__(self) -> str:
        return f"oneai.Collection({self.name})"
