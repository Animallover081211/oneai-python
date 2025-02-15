import pytest
import oneai

collection = oneai.clustering.Collection("test-collection", api_key=oneai.api_key)
cluster: oneai.clustering.Cluster = None
phrase: oneai.clustering.Phrase = None

items = [
    "Can not access account",
    "I cannot access my account",
    "Can not enter my account",
    "Cancel order",
    "I want to cancel my order",
    "How do I cancel my order?",
    "Need help cancelling order",
]


def test_add_items():
    assert "status" in collection.add_items(items)


def test_get_collections():
    collec = next(oneai.clustering.get_collections(limit=1, api_key=oneai.api_key))
    assert collec.id


@pytest.mark.dependency()
def test_get_clusters():
    global cluster

    cluster = next(collection.get_clusters(limit=1))
    assert cluster.collection


@pytest.mark.dependency(depends=["test_get_clusters"])
def test_get_phrases():
    global phrase

    phrase = next(cluster.get_phrases(limit=1))
    assert phrase.cluster


@pytest.mark.dependency(depends=["test_get_phrases"])
def test_get_items():
    item: oneai.clustering.Item = next(phrase.get_items(limit=1))
    assert item.phrase


def test_empty_collection():
    assert (
        next(
            oneai.clustering.Collection(
                "empty-collection-keep-empty", api_key=oneai.api_key
            ).get_clusters(),
            None,
        )
        == None
    )
