"""Write the saved lesson plans in dsa_explainer/plans/ from the specs below.

    python backend/scripts/author_plans.py            # write every plan
    python backend/scripts/author_plans.py dfs        # just one

Each spec gives the data, the operations, the narration and the quiz. The script
runs the real simulator to fill in every claimed_state, computes every quiz
answer and checks it is one of the options, then runs the full verifier. A plan
that fails is reported and not written. The narration was written by Claude
(Anthropic) for this project; the verifier, not the author, vouches for it.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dsa_explainer import algorithms, config  # noqa: E402
from dsa_explainer.core.lesson import Lesson, Op, Question, Scene  # noqa: E402
from dsa_explainer.core.verifier import question_answer, verify_lesson  # noqa: E402

AUTHOR = "Claude (Anthropic), hand-written for DSA Explainer"


def q(question, start, ops, ask, options, explanation):
    return {"question": question, "start": start, "ops": ops, "ask": ask, "options": options,
            "explanation": explanation}


PLANS = {
    # ------------------------------------------------------------------ linear
    "deque": dict(
        title="Deques: Both Ends Open", level="beginner",
        topic="How does a deque (double-ended queue) work?",
        initial=[4, 6],
        intro=("A line you can join at both ends",
               "A deque is a double ended queue. Think of a line where people may join or leave at either end. "
               "Ours starts with 4 at the front and 6 at the rear, and every operation touches one of the two ends."),
        steps=[
            ("push_back", {"value": 9}, "push_back(9)",
             "First we push 9 onto the back, exactly like joining an ordinary queue. The deque now holds 4, 6 "
             "and 9, and the rear is 9."),
            ("push_front", {"value": 2}, "push_front(2)",
             "Now something a queue cannot do: we push 2 onto the front. The front is now 2, and the size is 4."),
            ("pop_back", {}, "pop_back()",
             "Pop back removes the value at the rear, which is 9. That end behaves like the top of a stack, so "
             "the rear is now 6."),
            ("pop_front", {}, "pop_front()",
             "Pop front removes 2 from the front, just like dequeuing. The front is 4 again and the size is 2."),
            ("push_front", {"value": 7}, "push_front(7)",
             "Finally we push 7 at the front. Every push and pop here took the same short time, because we only "
             "ever touch an end. The deque holds 7, 4 and 6."),
        ],
        summary=(["Push and pop at both the front and the rear", "Every end operation takes O(1) time",
                  "One end acts like a stack, both ends like a queue"],
                 "A deque gives you a stack and a queue in one structure. Use it for sliding windows, undo "
                 "histories and any job that needs both ends."),
        quiz=[
            q("A deque holds 1 then 5. We push_front 3, push_back 8, then pop_front. What is at the front?",
              [1, 5], [("push_front", {"value": 3}), ("push_back", {"value": 8}), ("pop_front", {})], "front",
              ["3", "1", "5", "8"], "Pop front removes the 3 we just pushed, so 1 is at the front again."),
            q("A deque holds 2, 6 and 4. We pop_back, then push_front 9. What does it hold, front to rear?",
              [2, 6, 4], [("pop_back", {}), ("push_front", {"value": 9})], "items",
              ["9, 2, 6", "2, 6, 9", "9, 2, 4", "6, 2, 9"], "Pop back removes 4, then 9 joins at the front."),
        ],
    ),
    # ------------------------------------------------------------------ trees
    "tree_traversal": dict(
        title="In-Order Traversal, Step by Step", level="beginner",
        topic="Show an in-order traversal of a binary search tree",
        initial={"values": [8, 3, 10, 1, 6, 14], "order": "inorder"},
        intro=("Left, node, right",
               "A traversal visits every node of a tree exactly once. In order means: first the whole left "
               "subtree, then the node itself, then the right subtree. On a binary search tree that lists the "
               "values from smallest to largest."),
        steps=[
            ("visit", {}, "visit 1",
             "From 8 we go left to 3, then left again to 1. It has no left child, so 1 is visited first."),
            ("visit", {}, "visit 3",
             "The left subtree of 3 is done, so now we visit 3 itself, before going to its right side."),
            ("visit", {}, "visit 6",
             "Next comes the right subtree of 3, which is just the node 6. That finishes everything on the left "
             "of 8."),
            ("visit", {}, "visit 8",
             "With the whole left side done, we visit 8. Notice the order so far: 1, 3, 6, 8, already sorted."),
            ("visit", {}, "visit 10",
             "Now the right subtree of 8. Its smallest node is 10, which has no left child, so 10 is next."),
            ("visit", {}, "visit 14",
             "Last comes 14, the right child of 10. Every node was visited once, in increasing order."),
        ],
        summary=(["In-order: left subtree, node, right subtree", "On a BST it lists values in sorted order",
                  "Every node is visited once: O(n)"],
                 "In-order traversal gave us 1, 3, 6, 8, 10 and 14. Pre-order and post-order use the same walk but "
                 "visit the node before or after its children."),
        quiz=[
            q("Insert 5, 3, 8, 2 and 4 into a BST. A pre-order traversal visits three nodes. Which ones, in order?",
              {"values": [5, 3, 8, 2, 4], "order": "preorder"}, [("visit", {})] * 3, "visited",
              ["5, 3, 2", "2, 3, 4", "5, 3, 8", "3, 2, 4"],
              "Pre-order visits a node before its children: 5, then its left child 3, then 2."),
            q("Insert 5, 3, 8, 2 and 4 into a BST. What is its full post-order traversal?",
              {"values": [5, 3, 8, 2, 4], "order": "postorder"}, [], "order",
              ["2, 4, 3, 8, 5", "2, 3, 4, 5, 8", "5, 3, 2, 4, 8", "2, 4, 8, 3, 5"],
              "Post-order visits both children first, so the root 5 comes last."),
        ],
    ),
    "min_heap": dict(
        title="Min-Heaps and Priority Queues", level="intermediate",
        topic="How does a min-heap priority queue insert and extract?",
        initial=[3, 8, 5],
        intro=("The smallest value lives at the root",
               "A min-heap is a complete binary tree where every parent is smaller than its children, stored level "
               "by level in an array. Our heap holds 3, 8 and 5, so the root is 3."),
        steps=[
            ("insert", {"value": 1}, "insert(1): sift up",
             "Insert 1 goes into the next free slot, under 8. It is smaller than its parent, so they swap, and "
             "then it beats 3 too. After sifting up, the root is 1."),
            ("insert", {"value": 6}, "insert(6)",
             "Insert 6 lands under 3. Since 6 is larger than its parent, the heap property already holds and no "
             "swap is needed."),
            ("extract_min", {}, "extract_min(): sift down",
             "Extract min removes the root 1. The last value, 6, moves to the root and sinks: it swaps with its "
             "smaller child 3. The root is now 3."),
            ("extract_min", {}, "extract_min()",
             "Extract min again removes 3. The value 8 moves up to the root and swaps with its smaller child 5, "
             "so the root is 5."),
            ("insert", {"value": 2}, "insert(2): all the way up",
             "Finally insert 2. It swaps with 6, then with 5, rising all the way to the top. The root is 2, the "
             "smallest value, as always."),
        ],
        summary=(["Every parent is smaller than its children", "Insert sifts up, extract min sifts down",
                  "Both take O(log n) swaps; peek is O(1)"],
                 "A heap only keeps the smallest value at the top, which is exactly what a priority queue needs, "
                 "for example to pick the next task or the next node in Dijkstra's algorithm."),
        quiz=[
            q("A min-heap is built by inserting 4 then 9. Then 1 is inserted. What is the root?",
              [4, 9], [("insert", {"value": 1})], "root", ["1", "4", "9", "2"],
              "1 is smaller than its parent 4, so it sifts up to the root."),
            q("A min-heap holds 2, 7 and 4. After one extract min, what is the array?",
              [2, 7, 4], [("extract_min", {})], "items", ["4, 7", "7, 4", "2, 7", "4, 2, 7"],
              "4 moves to the root and is already smaller than 7, so it stays."),
        ],
    ),
    "heap_sort": dict(
        title="Heap Sort in Place", level="advanced",
        topic="Explain heap sort on the array 4, 10, 3, 5, 1, 8",
        initial=[4, 10, 3, 5, 1, 8],
        intro=("Heapify, then extract the maximum",
               "Heap sort works in two phases on the same array. First it builds a max heap, where every parent "
               "is larger than its children. Then it moves the root, the largest value, to the end, again and "
               "again."),
        steps=[
            ("build_heap", {}, "build_heap()",
             "Build heap sifts down from the last parent to the root. 3 swaps with 8, then 4 sinks below 10 and "
             "5. The array becomes a max heap and the root is 10."),
            ("extract_max", {}, "extract_max(): 10 to the end",
             "Swap the root 10 with the last value 3, so 10 is in its final place. The heap shrinks by one, and 3 "
             "sinks below 8. The root is now 8."),
            ("extract_max", {}, "extract_max(): 8 to the end",
             "Swap 8 with 1, and 8 joins the sorted part. 1 sinks past 5 and 4, so the root is 5."),
            ("extract_max", {}, "extract_max(): 5 to the end",
             "Swap 5 with 1. Then 1 sinks below 4, and 4 becomes the root."),
            ("extract_max", {}, "extract_max(): 4 to the end",
             "Swap 4 with 3. The heap now holds just 3 and 1, and 3 is already larger, so nothing sinks."),
            ("extract_max", {}, "extract_max(): done",
             "One last swap puts 3 in place, leaving 1 at the front. The array reads 1, 3, 4, 5, 8, 10."),
        ],
        summary=(["Build a max heap in O(n)", "Swap the root to the end and sift down, n times",
                  "O(n log n) always, and O(1) extra space"],
                 "Heap sort never needs a second array and always takes n log n time. The sorted part grew from the "
                 "back while the heap shrank from the front."),
        quiz=[
            q("Heap sort starts on the array 2, 9, 4. After build heap, what is the root?",
              [2, 9, 4], [("build_heap", {})], "root", ["9", "2", "4", "3"],
              "9 is the largest value, and a max heap keeps it at the root."),
            q("Heap sort runs build heap, then one extract max, on 2, 9, 4. What is the array now?",
              [2, 9, 4], [("build_heap", {}), ("extract_max", {})], "items",
              ["4, 2, 9", "2, 4, 9", "9, 2, 4", "4, 9, 2"],
              "9 swaps to the end; 4 at the root is already larger than 2."),
        ],
    ),
    # ------------------------------------------------------------------ graphs
    "dfs": dict(
        title="Depth-First Search and Backtracking", level="intermediate",
        topic="Show depth-first search on a tree-shaped graph from A",
        initial={"edges": [["A", "B"], ["A", "C"], ["B", "D"], ["B", "E"], ["C", "F"]], "start": "A"},
        intro=("Go deep, then back up",
               "Depth first search follows one path as far as it can, then backs up to the last node that still "
               "has somewhere new to go. A stack holds the path we are on. We start at A and take neighbours in "
               "alphabetical order."),
        steps=[
            ("dfs_step", {}, "visit A",
             "We visit A and put it on the stack. The current node is A."),
            ("dfs_step", {}, "A to B",
             "A's first unvisited neighbour is B, so we go deeper to B and push it. The top of the stack is B."),
            ("dfs_step", {}, "B to D",
             "From B we go on to D. The stack now holds the whole path: A, B, D."),
            ("dfs_step", {}, "back to B, then E",
             "D has nowhere new to go, so we pop it and back up to B. B still has E, so we visit E next."),
            ("dfs_step", {}, "back to A, then C",
             "E is a dead end and so is B now. We pop both and back up to A, whose next neighbour is C."),
            ("dfs_step", {}, "C to F",
             "From C we reach F. Every node has been visited, in the order A, B, D, E, C, F."),
        ],
        summary=(["Follow one path as deep as it goes", "A stack remembers the way back",
                  "Visits every reachable node in O(V + E)"],
                 "The stack is the same as the call stack of a recursive search. Depth first search finds paths, "
                 "connected parts and cycles, and it is the base of topological sorting."),
        quiz=[
            q("A graph has edges A-B, A-C and B-D. Depth first search from A takes four steps. In what order are "
              "the nodes visited?",
              {"edges": [["A", "B"], ["A", "C"], ["B", "D"]], "start": "A"}, [("dfs_step", {})] * 4, "visited",
              ["A, B, D, C", "A, B, C, D", "A, C, B, D", "A, D, B, C"],
              "From B the search goes deeper to D before it backs up to C."),
            q("A graph has edges A-B, B-C and A-D. After three depth first steps from A, which node is on top of "
              "the stack?",
              {"edges": [["A", "B"], ["B", "C"], ["A", "D"]], "start": "A"}, [("dfs_step", {})] * 3, "top",
              ["C", "A", "B", "D"], "The path is A, B, C, so C is on top."),
        ],
    ),
    "dijkstra": dict(
        title="Dijkstra's Shortest Paths", level="advanced",
        topic="Find shortest paths from A with Dijkstra's algorithm",
        initial={"edges": [["A", "B", 4], ["A", "C", 1], ["C", "B", 2], ["B", "D", 5], ["C", "D", 8]],
                 "start": "A"},
        intro=("Settle the closest node first",
               "Dijkstra's algorithm finds the shortest distance from A to every node. A starts at 0 and every "
               "other node at infinity. Each step settles the closest unsettled node, then checks whether going "
               "through it shortens the route to its neighbours."),
        steps=[
            ("settle", {}, "settle A (0)",
             "A is closest, at 0, so we settle it. Its edges give B a distance of 4 and C a distance of 1."),
            ("settle", {}, "settle C (1)",
             "C at 1 is now the closest unsettled node. Going through C, B costs 1 plus 2, which is 3, better "
             "than 4. D gets 1 plus 8, which is 9."),
            ("settle", {}, "settle B (3)",
             "B at 3 is next. Through B, D costs 3 plus 5, which is 8, better than 9, so D drops to 8."),
            ("settle", {}, "settle D (8)",
             "Finally we settle D at 8. Every node is settled: A 0, C 1, B 3 and D 8."),
        ],
        summary=(["Settle the unsettled node with the smallest distance", "Relax its edges: keep any shorter route",
                  "Needs weights that are not negative"],
                 "The direct edge from A to B cost 4, but the route through C cost only 3. Dijkstra's algorithm "
                 "finds such detours by always settling the closest node next."),
        quiz=[
            q("Edges: A-B weight 5, A-C weight 2, B-C weight 1. Dijkstra runs from A until three nodes are "
              "settled. What is the distance to B?",
              {"edges": [["A", "B", 5], ["A", "C", 2], ["B", "C", 1]], "start": "A"}, [("settle", {})] * 3,
              "dist_B", ["3", "5", "2", "6"], "Going through C costs 2 plus 1, which is 3, less than 5."),
            q("Edges: A-B weight 5, A-C weight 2, B-C weight 1. After two settle steps from A, which nodes are "
              "settled, in order?",
              {"edges": [["A", "B", 5], ["A", "C", 2], ["B", "C", 1]], "start": "A"}, [("settle", {})] * 2,
              "settled", ["A, C", "A, B", "A, B, C", "C, A"], "After A, C is the closest node at 2."),
        ],
    ),
    "topological_sort": dict(
        title="Topological Sort with Kahn's Algorithm", level="advanced",
        topic="Order tasks with dependencies using a topological sort",
        initial={"edges": [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"]]},
        intro=("Do every task after what it depends on",
               "Each arrow means one task must come before another: A before B and C, and both B and C before D. "
               "Kahn's algorithm keeps the tasks whose arrows into them are all gone as ready, and takes the "
               "alphabetically first one each step."),
        steps=[
            ("take", {}, "take A",
             "Only A has no incoming arrows, so A is taken first. Removing its arrows frees both B and C, which "
             "become ready."),
            ("take", {}, "take B",
             "B and C are ready, and B comes first alphabetically. Removing the arrow from B leaves D with just "
             "one incoming arrow."),
            ("take", {}, "take C",
             "C is taken next. Its arrow to D was the last one, so D becomes ready."),
            ("take", {}, "take D",
             "Finally D is taken. The order A, B, C, D respects every arrow."),
        ],
        summary=(["Ready: tasks with no remaining incoming arrows", "Take one, remove its arrows, repeat",
                  "If nothing is ready but tasks remain, there is a cycle"],
                 "A topological order only exists for graphs without cycles. Build tools, course plans and "
                 "spreadsheet formulas all rely on it."),
        quiz=[
            q("Arrows: A to C, B to C, C to D, B to E. After taking two tasks, which tasks are ready?",
              {"edges": [["A", "C"], ["B", "C"], ["C", "D"], ["B", "E"]]}, [("take", {})] * 2, "ready",
              ["C, E", "C", "E", "D, E"], "Taking A and B removes every arrow into C and E."),
            q("Arrows: B to A and C to A. Before any step, which tasks are ready?",
              {"edges": [["B", "A"], ["C", "A"]]}, [], "ready", ["B, C", "A", "A, B, C", "C, B"],
              "B and C have no incoming arrows; A waits for both."),
        ],
    ),
    # ------------------------------------------------------------------ sorting
    "bubble_sort": dict(
        title="Bubble Sort, Pass by Pass", level="beginner",
        topic="How does bubble sort work on 5, 1, 4, 2, 8, 3?",
        initial=[5, 1, 4, 2, 8, 3],
        intro=("Big values bubble to the end",
               "Bubble sort walks along the array comparing neighbours and swapping any pair that is out of "
               "order. After each pass, the largest value that is not yet in place has bubbled to the end."),
        steps=[
            ("bubble_pass", {}, "pass 1: 8 bubbles to the end",
             "In the first pass, 5 swaps past 1, 4 and 2, and later 8 swaps past 3. That is 4 swaps, and 8 is now "
             "in its final place at the end."),
            ("bubble_pass", {}, "pass 2: 5 is placed",
             "The second pass swaps 4 with 2 and 5 with 3. Now 5 sits in place before 8."),
            ("bubble_pass", {}, "pass 3: 4 is placed",
             "The third pass needs just one swap, 4 with 3. The array reads 1, 2, 3, 4, 5, 8."),
            ("bubble_pass", {}, "pass 4: no swaps, stop",
             "The fourth pass compares the first values and swaps nothing. No swaps means the array is sorted, so "
             "bubble sort stops early."),
        ],
        summary=(["Compare neighbours, swap if out of order", "Each pass places the largest unsorted value",
                  "O(n squared), but it stops early on sorted input"],
                 "Bubble sort is simple to follow but slow on large arrays. Its early stop makes it quick when the "
                 "array is already nearly sorted."),
        quiz=[
            q("Bubble sort makes one pass over 3, 1, 2. How many swaps does it make?",
              [3, 1, 2], [("bubble_pass", {})], "swaps", ["2", "1", "3", "0"],
              "3 swaps past 1, then past 2, so there are 2 swaps."),
            q("Bubble sort makes one pass over 4, 3, 2, 1. What is the array afterwards?",
              [4, 3, 2, 1], [("bubble_pass", {})], "items",
              ["3, 2, 1, 4", "1, 2, 3, 4", "3, 4, 2, 1", "4, 3, 2, 1"],
              "4 bubbles all the way to the end; the rest keep their order."),
        ],
    ),
    "insertion_sort": dict(
        title="Insertion Sort, Card by Card", level="beginner",
        topic="Explain insertion sort like sorting playing cards",
        initial=[5, 2, 4, 6, 1, 3],
        intro=("Slide each card into place",
               "Insertion sort works like sorting cards in your hand. The left part is always sorted. Each step "
               "takes the next value and slides it left past every larger value."),
        steps=[
            ("insert_next", {}, "insert 2",
             "The first card, 5, is sorted on its own. The key 2 is smaller, so 5 shifts right and 2 goes in "
             "front."),
            ("insert_next", {}, "insert 4",
             "The key 4 is smaller than 5 but larger than 2, so 5 shifts right and 4 drops in between."),
            ("insert_next", {}, "insert 6",
             "The key 6 is larger than everything sorted so far, so nothing shifts. The sorted part is 2, 4, 5, 6."),
            ("insert_next", {}, "insert 1",
             "The key 1 is the smallest yet. All 4 sorted values shift right, and 1 goes to the very front."),
            ("insert_next", {}, "insert 3",
             "The last key 3 slides past 6, 5 and 4, and stops after 2. The array is sorted."),
        ],
        summary=(["Grow a sorted part on the left", "Shift larger values right, drop the key in the gap",
                  "Fast on nearly sorted input, O(n squared) at worst"],
                 "Insertion sort did very little work for 6, which was already in place, and the most for 1. That "
                 "is why it shines on small or nearly sorted data."),
        quiz=[
            q("Insertion sort inserts one key into 3, 1, 2. What is the array afterwards?",
              [3, 1, 2], [("insert_next", {})], "items", ["1, 3, 2", "1, 2, 3", "3, 1, 2", "3, 2, 1"],
              "The key 1 slides in front of 3; 2 has not been inserted yet."),
            q("Insertion sort runs two steps on 4, 5, 1. How many values shift in the second step?",
              [4, 5, 1], [("insert_next", {}), ("insert_next", {})], "shifts", ["2", "1", "0", "3"],
              "The key 1 is smaller than both 4 and 5, so 2 values shift."),
        ],
    ),
    "selection_sort": dict(
        title="Selection Sort: Pick the Smallest", level="beginner",
        topic="Show selection sort on 64, 25, 12, 22, 11",
        initial=[64, 25, 12, 22, 11],
        intro=("Find the smallest, put it next",
               "Selection sort builds the sorted part from the left. Each step scans the unsorted part for its "
               "smallest value and swaps it into the next position."),
        steps=[
            ("select_next", {}, "select 11",
             "The smallest value of all is 11, at the far end. It swaps places with 64 and starts the sorted part."),
            ("select_next", {}, "select 12",
             "Among 25, 12, 22 and 64, the smallest is 12. It swaps with 25."),
            ("select_next", {}, "select 22",
             "Next the smallest of 25, 22 and 64 is 22, which swaps with 25."),
            ("select_next", {}, "select 25: already in place",
             "The smallest of 25 and 64 is 25, and it is already in the right spot, so no swap is needed. The "
             "last value, 64, is in place too."),
        ],
        summary=(["Scan the unsorted part for its smallest value", "Swap it to the front of that part",
                  "Always O(n squared) comparisons, at most n minus 1 swaps"],
                 "Selection sort makes few swaps, which helps when writing is expensive, but it always scans the "
                 "whole unsorted part."),
        quiz=[
            q("Selection sort runs one step on 3, 1, 2. Which value does it select?",
              [3, 1, 2], [("select_next", {})], "selected", ["1", "2", "3", "0"],
              "1 is the smallest value in the whole array."),
            q("Selection sort runs one step on 5, 4, 3. What is the array afterwards?",
              [5, 4, 3], [("select_next", {})], "items", ["3, 4, 5", "4, 5, 3", "3, 5, 4", "5, 4, 3"],
              "3 swaps with 5, and the array happens to be sorted."),
        ],
    ),
    "merge_sort": dict(
        title="Merge Sort, Bottom Up", level="intermediate",
        topic="Explain merge sort on 5, 1, 4, 2, 8, 3",
        initial=[5, 1, 4, 2, 8, 3],
        intro=("Merge small sorted runs into bigger ones",
               "Merge sort treats every single value as a sorted run. It merges neighbouring runs of width 1 into "
               "pairs, then pairs into fours, and so on, until one run holds everything."),
        steps=[
            ("merge_next", {}, "merge 5 | 1",
             "The first two runs, 5 and 1, merge into the sorted pair 1, 5."),
            ("merge_next", {}, "merge 4 | 2",
             "Next, 4 and 2 merge into 2, 4."),
            ("merge_next", {}, "merge 8 | 3",
             "Then 8 and 3 become 3, 8. Every run now has width 2."),
            ("merge_next", {}, "merge 1 5 | 2 4",
             "Now we merge runs of width 2. Taking the smaller front value each time, 1, 5 and 2, 4 become 1, 2, "
             "4, 5. The run 3, 8 has no partner yet, so it waits."),
            ("merge_next", {}, "merge 1 2 4 5 | 3 8",
             "Last, the run of 4 merges with 3, 8. The array is 1, 2, 3, 4, 5, 8."),
        ],
        summary=(["Every merge takes two sorted runs", "Widths double: 1, 2, 4",
                  "O(n log n) every time, with O(n) extra space"],
                 "Merging only ever compares the front values of two sorted runs, so each round is one quick pass, "
                 "and there are about log n rounds."),
        quiz=[
            q("Merge sort performs two merges on 4, 3, 2, 1. What is the array afterwards?",
              [4, 3, 2, 1], [("merge_next", {})] * 2, "items",
              ["3, 4, 1, 2", "1, 2, 3, 4", "3, 4, 2, 1", "4, 3, 1, 2"],
              "The pairs 4, 3 and 2, 1 each become sorted."),
            q("Merge sort performs three merges on 4, 3, 2, 1. What was the run width of the third merge?",
              [4, 3, 2, 1], [("merge_next", {})] * 3, "width", ["2", "1", "4", "3"],
              "The third merge joins two runs of width 2 into the final run."),
        ],
    ),
    "quick_sort": dict(
        title="Quick Sort and Partitioning", level="advanced",
        topic="Explain quick sort with a pivot on 5, 1, 4, 2, 8, 3",
        initial=[5, 1, 4, 2, 8, 3],
        intro=("Pick a pivot, split around it",
               "Quick sort picks a pivot, here the last value of the range. It moves every smaller value before "
               "the pivot, which puts the pivot in its final place, then sorts each side the same way."),
        steps=[
            ("partition_next", {}, "partition all, pivot 3",
             "The pivot is 3. The smaller values 1 and 2 move to the front, and 3 lands right after them at index "
             "2, its final place."),
            ("partition_next", {}, "partition left, pivot 2",
             "Now the left part, 1 and 2. The pivot is 2, and 1 is already smaller, so 2 stays at index 1. Both "
             "are in place."),
            ("partition_next", {}, "partition right, pivot 4",
             "On the right, 5, 8 and 4, the pivot is 4. Nothing is smaller, so 4 swaps to the front of the range."),
            ("partition_next", {}, "partition 8 | 5, pivot 5",
             "The last range holds 8 and 5. The pivot is 5, which swaps in front of 8. The array is sorted."),
        ],
        summary=(["The pivot ends in its final place", "Smaller values go left, the rest go right",
                  "O(n log n) on average, O(n squared) at worst"],
                 "Each partition fixed one pivot for good and split the work in two. A bad pivot, like the largest "
                 "value every time, is what makes the worst case slow."),
        quiz=[
            q("Quick sort partitions 3, 1, 2 once, using the last value as the pivot. At which index does the pivot "
              "end up?",
              [3, 1, 2], [("partition_next", {})], "pivot_index", ["1", "0", "2", "3"],
              "Only 1 is smaller than the pivot 2, so 2 ends at index 1."),
            q("Quick sort partitions 4, 7, 2, 5 once, with the last value as the pivot. What is the array afterwards?",
              [4, 7, 2, 5], [("partition_next", {})], "items",
              ["4, 2, 5, 7", "2, 4, 5, 7", "4, 5, 2, 7", "5, 4, 2, 7"],
              "4 and 2 are smaller than 5 and keep their order; 5 goes right after them."),
        ],
    ),
    # ------------------------------------------------------------------ searching
    "linear_search": dict(
        title="Linear Search", level="beginner",
        topic="How does linear search find 4 in 7, 3, 9, 4, 6?",
        initial={"array": [7, 3, 9, 4, 6], "target": 4},
        intro=("Look at each value in turn",
               "Linear search is the most direct way to find something: check the first value, then the next, and "
               "so on, until you find the target or run out. Here the target is 4."),
        steps=[
            ("check_next", {}, "check index 0: 7",
             "Index 0 holds 7, which is not 4, so we move on."),
            ("check_next", {}, "check index 1: 3",
             "Index 1 holds 3. Still not the target."),
            ("check_next", {}, "check index 2: 9",
             "Index 2 holds 9. The array is not sorted, so we cannot skip anything; we keep going."),
            ("check_next", {}, "check index 3: found 4",
             "Index 3 holds 4, the target. The search stops after 4 checks."),
        ],
        summary=(["Check values one by one from the start", "Works on any array, sorted or not",
                  "O(n) checks in the worst case"],
                 "Linear search needed 4 checks here. If the target were missing, it would have checked all 5 "
                 "values before giving up."),
        quiz=[
            q("Linear search looks for 6 in 5, 2, 8, 1 and checks every value. Was 6 found?",
              {"array": [5, 2, 8, 1], "target": 6}, [("check_next", {})] * 4, "found", ["no", "yes"],
              "6 is not in the array, so all four checks fail."),
            q("Linear search looks for 1 in 4, 8, 1, 5. At which index does it stop?",
              {"array": [4, 8, 1, 5], "target": 1}, [("check_next", {})] * 3, "index", ["2", "3", "1", "0"],
              "1 sits at index 2, the third value checked."),
        ],
    ),
    "binary_search": dict(
        title="Binary Search: Halve and Conquer", level="intermediate",
        topic="Find 38 in a sorted array with binary search",
        initial={"array": [2, 5, 8, 12, 16, 23, 38, 56], "target": 38},
        intro=("Check the middle, drop half",
               "Binary search needs a sorted array. It looks at the middle of the current range: if the middle "
               "value is too small, the target can only be on the right; if too large, only on the left. Here we "
               "look for 38."),
        steps=[
            ("probe", {}, "mid = 3: 12 < 38",
             "The range is index 0 to 7, so mid is 3. The middle value is 12, smaller than 38, so we drop the left "
             "half and low becomes 4."),
            ("probe", {}, "mid = 5: 23 < 38",
             "Now the range is 4 to 7 and mid is 5. The middle value is 23, still too small, so low becomes 6."),
            ("probe", {}, "mid = 6: found 38",
             "The range is 6 to 7, so mid is 6. The middle value is 38. Found it, in just 3 checks."),
        ],
        summary=(["Needs a sorted array", "Each check halves the range",
                  "O(log n): 8 values take at most 4 checks"],
                 "Linear search might have needed 7 checks to reach 38. Binary search needed 3, and the gap grows "
                 "quickly with bigger arrays."),
        quiz=[
            q("Binary search looks for 7 in 1, 3, 5, 7, 9. After the first probe, what is low?",
              {"array": [1, 3, 5, 7, 9], "target": 7}, [("probe", {})], "low", ["3", "2", "0", "4"],
              "The middle value 5 is too small, so low moves to index 3."),
            q("Binary search looks for 5 in 2, 4, 6, 8, 10, 12. After the first probe, what is high?",
              {"array": [2, 4, 6, 8, 10, 12], "target": 5}, [("probe", {})], "high", ["1", "2", "5", "0"],
              "The middle value 6 is too large, so high moves to index 1."),
        ],
    ),
    # ------------------------------------------------------------------ hashing
    "hash_table": dict(
        title="Hash Tables and Collisions", level="intermediate",
        topic="How does a hash table with chaining handle collisions?",
        initial={"buckets": 5, "keys": [12, 7]},
        intro=("Jump straight to the right bucket",
               "A hash table turns each key into a bucket number. Ours has 5 buckets and uses the key mod 5. The "
               "keys 12 and 7 both landed in bucket 2, a collision, so they share a chain."),
        steps=[
            ("insert", {"key": 3}, "insert 3: bucket 3",
             "3 mod 5 is 3, so the key 3 goes straight into the empty bucket 3."),
            ("insert", {"key": 17}, "insert 17: bucket 2",
             "17 mod 5 is 2, another collision. 17 joins the end of the chain in bucket 2, after 12 and 7."),
            ("search", {"key": 7}, "search 7",
             "To find 7 we only look in bucket 2 and walk its chain: 12, then 7. Found, without touching any "
             "other bucket."),
            ("delete", {"key": 12}, "delete 12",
             "Deleting 12 also starts at bucket 2. We remove it from the chain, which now holds 7 and 17. The "
             "size is 3."),
            ("search", {"key": 10}, "search 10: not found",
             "10 mod 5 is 0, and bucket 0 is empty, so we know at once that 10 is not in the table."),
        ],
        summary=(["The hash picks the bucket: key mod 5", "Colliding keys share a chain",
                  "O(1) on average, O(n) if every key collides"],
                 "A good hash function spreads keys evenly, so chains stay short and lookups stay fast."),
        quiz=[
            q("A table with 4 buckets holds 5 and 9. We insert 13, using key mod 4. Which keys are in its bucket?",
              {"buckets": 4, "keys": [5, 9]}, [("insert", {"key": 13})], "chain",
              ["5, 9, 13", "13", "13, 5, 9", "5, 13"], "5, 9 and 13 all leave remainder 1 when divided by 4."),
            q("A table with 7 buckets holds 10 and 3. Into which bucket does 24 go, using key mod 7?",
              {"buckets": 7, "keys": [10, 3]}, [("insert", {"key": 24})], "bucket", ["3", "4", "6", "0"],
              "24 mod 7 is 3."),
        ],
    ),
    # ------------------------------------------------------------------ dynamic programming
    "fibonacci": dict(
        title="Fibonacci with a Table", level="beginner",
        topic="Explain Fibonacci with dynamic programming",
        initial={"n": 7},
        intro=("Remember answers instead of recomputing",
               "Each Fibonacci number is the sum of the two before it. Computing them by plain recursion repeats "
               "the same work again and again. Instead we fill a table from the start: F of 0 is 0 and F of 1 is "
               "1."),
        steps=[
            ("fill_next", {}, "F(2) = F(1) + F(0)",
             "F of 2 adds the two cells before it: 1 plus 0 gives 1."),
            ("fill_next", {}, "F(3) = F(2) + F(1)",
             "F of 3 is 1 plus 1, which is 2. We read both from the table instead of recomputing them."),
            ("fill_next", {}, "F(4) = F(3) + F(2)",
             "F of 4 is 2 plus 1, so 3."),
            ("fill_next", {}, "F(5) = F(4) + F(3)",
             "F of 5 is 3 plus 2, which is 5."),
            ("fill_next", {}, "F(6) = F(5) + F(4)",
             "F of 6 is 5 plus 3, giving 8."),
            ("fill_next", {}, "F(7) = F(6) + F(5)",
             "Finally F of 7 is 8 plus 5, which is 13. Each cell took a single addition."),
        ],
        summary=(["Store each answer in a table", "Build from the smallest cases up",
                  "O(n) time instead of exponential"],
                 "The table turned an exponential recursion into 6 quick additions. That is the core idea of "
                 "dynamic programming: solve each smaller problem once and reuse it."),
        quiz=[
            q("A Fibonacci table up to F of 5 starts with F of 0 and F of 1. After filling two more cells, what is "
              "the value just filled?",
              {"n": 5}, [("fill_next", {})] * 2, "value", ["2", "1", "3", "5"],
              "The second cell filled is F of 3, which is 1 plus 1."),
            q("A Fibonacci table up to F of 6 starts with F of 0 and F of 1. After filling four more cells, what "
              "is the value just filled?",
              {"n": 6}, [("fill_next", {})] * 4, "value", ["5", "3", "8", "4"],
              "The fourth cell filled is F of 5, which is 3 plus 2."),
        ],
    ),
    "coin_change": dict(
        title="Coin Change: Fewest Coins", level="advanced",
        topic="Find the fewest coins for 6 with coins 1, 3 and 4",
        initial={"coins": [1, 3, 4], "amount": 6},
        intro=("Solve every smaller amount first",
               "We want to pay 6 with as few coins as possible, using coins of 1, 3 and 4. Cell a of the table will "
               "hold the fewest coins for amount a. Paying 0 takes 0 coins."),
        steps=[
            ("fill_next", {}, "amount 1",
             "For 1 only the 1 coin fits: 1 coin plus the 0 coins for amount 0 gives 1."),
            ("fill_next", {}, "amount 2",
             "For 2 again only the 1 coin fits, plus the best for amount 1, so 2 coins."),
            ("fill_next", {}, "amount 3",
             "For 3 the 3 coin fits, plus 0 coins for amount 0. So 1 coin beats the 3 coins of value 1."),
            ("fill_next", {}, "amount 4",
             "For 4 the 4 coin alone does it, so the best is 1 coin."),
            ("fill_next", {}, "amount 5",
             "For 5 the best is a 4 coin plus a 1 coin, or a 1 coin plus 4, so 2 coins."),
            ("fill_next", {}, "amount 6",
             "For 6, a 3 coin plus the best for 3, which is 1, gives 2 coins. A greedy choice of 4 first would need "
             "3 coins."),
        ],
        summary=(["Cell a holds the fewest coins for amount a", "Try each coin and look back in the table",
                  "Greedy can fail; dynamic programming is exact"],
                 "Paying 6 takes just 2 coins: 3 plus 3. Taking the biggest coin first would have given 4 plus 1 "
                 "plus 1, which is worse."),
        quiz=[
            q("Coins are 1, 2 and 5, and the table is filled up to amount 7. What is the fewest number of coins "
              "for 7?",
              {"coins": [1, 2, 5], "amount": 7}, [("fill_next", {})] * 7, "value", ["2", "3", "4", "1"],
              "A 5 coin and a 2 coin make 7."),
            q("Coins are 2 and 3, for amounts up to 4. After filling amount 1, what does its cell hold?",
              {"coins": [2, 3], "amount": 4}, [("fill_next", {})], "value", ["inf", "0", "1", "2"],
              "No coin is small enough to pay 1, so it cannot be paid."),
        ],
    ),
}


def make(name: str, spec: dict) -> Lesson:
    cls = algorithms.get(name)
    ds = cls(spec["initial"])
    caption, narration = spec["intro"]
    scenes = [Scene(kind="intro", caption=caption, narration=narration)]
    for op, args, caption, narration in spec["steps"]:
        ds.run(op, args)
        scenes.append(Scene(kind="step", caption=caption, narration=narration, op=Op(name=op, args=args),
                            claimed_state=ds.state()))
    points, narration = spec["summary"]
    scenes.append(Scene(kind="summary", caption="Summary", narration=narration, points=points))
    lesson = Lesson(topic=spec["topic"], level=spec["level"], title=spec["title"], structure=name,
                    initial=spec["initial"], scenes=scenes,
                    provenance={"author": AUTHOR, "written": date.today().isoformat(),
                                "checked_by": "DSA Explainer verifier (scripts/author_plans.py)"})
    for item in spec["quiz"]:
        question = Question(question=item["question"], start=item["start"],
                            ops=[Op(name=n, args=a) for n, a in item["ops"]], ask=item["ask"],
                            options=item["options"], answer="?", explanation=item["explanation"])
        question.answer = question_answer(lesson, question)
        if question.answer not in question.options:
            raise ValueError(f"{name}: the answer to '{question.question}' is {question.answer}, not an option")
        lesson.quiz.append(question)
    return lesson


def main(names: list[str]) -> int:
    failed = 0
    for name in names or PLANS:
        try:
            lesson = make(name, PLANS[name])
            report = verify_lesson(lesson)
        except Exception as exc:  # report every broken spec, keep going
            print(f"FAIL {name}: {exc}")
            failed += 1
            continue
        if not report.ok:
            print(f"FAIL {name}:\n  " + "\n  ".join(report.errors))
            failed += 1
            continue
        words = sum(len(s.narration.split()) for s in lesson.scenes)
        (config.PLANS_DIR / f"{name}.json").write_text(lesson.model_dump_json(indent=2, exclude_none=True) + "\n",
                                                        encoding="utf-8")
        print(f"ok   {name}: {report.checks} checks, {len(lesson.scenes)} scenes, {words} words")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
