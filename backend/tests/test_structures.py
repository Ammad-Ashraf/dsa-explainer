import pytest

from dsa_explainer.core.structures import BST, Graph, LinkedList, OpError, Queue, Stack, build


def test_stack_is_last_in_first_out():
    s = Stack([4, 9])
    s.run("push", {"value": 2})
    assert s.state() == [4, 9, 2] and s.facts()["top"] == 2
    s.run("pop")
    s.run("peek")
    assert s.state() == [4, 9] and s.facts()["size"] == 2


def test_impossible_operations_raise():
    with pytest.raises(OpError):
        Stack([]).run("pop")
    with pytest.raises(OpError):
        Stack([1]).run("push", {})  # missing value
    with pytest.raises(OpError):
        Stack([1]).run("enqueue", {"value": 1})  # not a stack operation
    with pytest.raises(OpError):
        Stack(list(range(7))).run("push", {"value": 1})  # too many to draw
    with pytest.raises(OpError):
        build("heap", [])


def test_queue_is_first_in_first_out():
    q = Queue([3, 8])
    q.run("enqueue", {"value": 5})
    q.run("dequeue")
    assert q.state() == [8, 5]
    assert q.facts()["front"] == 8 and q.facts()["rear"] == 5


def test_linked_list_insert_search_delete():
    ll = LinkedList([3, 8, 12])
    ll.run("insert_head", {"value": 1})
    ll.run("insert_at", {"index": 2, "value": 5})
    assert ll.state() == [1, 3, 5, 8, 12]
    assert len(ll.run("search", {"value": 8})) == 4  # the walk visits 1, 3, 5, 8
    ll.run("delete", {"value": 8})
    assert ll.state() == [1, 3, 5, 12] and ll.facts()["tail"] == 12
    with pytest.raises(OpError):
        ll.run("delete", {"value": 99})
    with pytest.raises(OpError):
        ll.run("insert_at", {"index": 9, "value": 1})


def test_bst_delete_with_two_children_uses_successor():
    t = BST([8, 3, 10, 1, 6, 14])
    t.run("delete", {"value": 3})
    assert t.facts()["preorder"] == [8, 6, 1, 10, 14]
    assert t.matches({"value": 8, "left": {"value": 6, "left": {"value": 1}},
                      "right": {"value": 10, "right": {"value": 14}}})
    assert t.facts()["inorder"] == [1, 6, 8, 10, 14]


def test_bst_rejects_duplicates_and_missing_values():
    t = BST([5])
    with pytest.raises(OpError):
        t.run("insert", {"value": 5})
    with pytest.raises(OpError):
        t.run("delete", {"value": 7})


def test_bfs_steps_and_order():
    g = Graph({"edges": [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"], ["C", "E"]], "start": "A"})
    assert g.facts()["bfs_order"] == ["A", "B", "C", "D", "E"]
    g.run("bfs_step")
    g.run("bfs_step")
    assert g.state() == {"current": "B", "queue": ["C", "D"], "visited": ["A", "B"]}
    for _ in range(3):
        g.run("bfs_step")
    with pytest.raises(OpError):
        g.run("bfs_step")  # queue is empty


def test_values_compare_as_text():
    assert Stack(["4", 9.0]).matches([4, "9"])
