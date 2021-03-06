"""
intervaltree: A mutable, self-balancing interval tree for Python 2 and 3.
Queries may be by point, by range overlap, or by range envelopment.

Test module: IntervalTree, Special methods

Copyright 2013-2017 Chaim-Leib Halbert

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from __future__ import absolute_import
from intervaltree import Interval, IntervalTree
import pytest
from test import data
try:
    import cPickle as pickle
except ImportError:
    import pickle


def test_update():
    t = IntervalTree()
    interval = Interval(0, 1)
    s = set([interval])

    t.update(s)
    assert isinstance(t, IntervalTree)
    assert len(t) == 1
    assert set(t).pop() == interval

    t.clear()
    assert not t
    t.extend(s)
    t.extend(s)
    assert isinstance(t, IntervalTree)
    assert len(t) == 1
    assert set(t).pop() == interval

    interval = Interval(2, 3)
    t.update([interval])
    assert isinstance(t, IntervalTree)
    assert len(t) == 2
    assert sorted(t)[1] == interval

    t = IntervalTree(s)
    t.extend([interval])
    assert isinstance(t, IntervalTree)
    assert len(t) == 2
    assert sorted(t)[1] == interval


def test_invalid_update():
    t = IntervalTree()

    with pytest.raises(ValueError):
        t.update([Interval(1, 0)])

    with pytest.raises(ValueError):
        t.update([Interval(1, 1)])

    with pytest.raises(ValueError):
        t.extend([Interval(1, 0)])

    with pytest.raises(ValueError):
        t.extend([Interval(1, 1)])


def test_union():
    t = IntervalTree()
    interval = Interval(0, 1)
    s = set([interval])

    # union with empty
    r = t.union(s)
    assert len(r) == 1
    assert set(r).pop() == interval

    # update with duplicates
    t.update(s)
    t.update(s)
    assert len(t) == 1
    assert set(t).pop() == interval

    # extend with duplicates
    t.extend(s)
    t.extend(s)
    assert len(t) == 1
    assert set(t).pop() == interval

    # update with non-dupe
    interval = Interval(2, 3)
    t.update([interval])
    assert len(t) == 2
    assert sorted(t)[1] == interval

    # extend with non-dupe
    t.remove(interval)
    assert len(t) == 1
    assert interval not in t
    t.extend([interval])
    assert len(t) == 2
    assert sorted(t)[1] == interval

    # commutativity with full overlaps, then no overlaps
    a = IntervalTree.from_tuples(data.ivs1.data)
    b = IntervalTree.from_tuples(data.ivs2.data)
    e = IntervalTree()

    aa = a.union(a)
    ae = a.union(e)
    ea = e.union(a)
    ee = e.union(e)
    aa.verify()
    ae.verify()
    ea.verify()
    ee.verify()
    assert aa == a
    assert ae == a
    assert ea == a
    assert ee == e

    ab = a.union(b)
    ba = b.union(a)
    ab.verify()
    ba.verify()
    assert ab == ba
    assert len(ab) == 109

    # commutativity with strict subset overlap
    aba = ab.union(a)
    abb = ab.union(b)
    bab = ba.union(b)
    baa = ba.union(a)
    aba.verify()
    abb.verify()
    bab.verify()
    baa.verify()
    assert aba == abb
    assert abb == bab
    assert bab == baa

    assert aba == ab

    # commutativity with partial overlap
    c = IntervalTree.from_tuples(data.ivs3.data)
    bc = b.union(c)
    cb = c.union(b)
    bc.verify()
    cb.verify()
    assert bc == cb
    assert len(bc) > len(b)
    assert len(bc) > len(c)
    assert len(bc) < len(b) + len(c)
    for iv in b:
        assert iv in bc
    for iv in c:
        assert iv in bc


def test_union_operator():
    t = IntervalTree()
    interval = Interval(0, 1)
    s = set([interval])

    # currently runs fine
    # with pytest.raises(TypeError):
    #     t | list(s)
    r = t | IntervalTree(s)
    assert len(r) == 1
    assert sorted(r)[0] == interval

    # also currently runs fine
    # with pytest.raises(TypeError):
    #     t |= s
    t |= IntervalTree(s)
    assert len(t) == 1
    assert sorted(t)[0] == interval


def test_invalid_union():
    t = IntervalTree()

    with pytest.raises(ValueError):
        t.union([Interval(1, 0)])


def test_invalid_update():
    t = IntervalTree()

    with pytest.raises(ValueError):
        t.update([Interval(1, 1)])


def test_difference():
    minuend = IntervalTree.from_tuples(data.ivs1.data)
    assert isinstance(minuend, IntervalTree)
    subtrahend = minuend.copy()
    expected_difference = IntervalTree([subtrahend.pop()])
    expected_difference.add(subtrahend.pop())

    minuend.verify()
    subtrahend.verify()
    expected_difference.verify()

    assert len(expected_difference) == len(minuend) - len(subtrahend)

    for iv in expected_difference:
        assert iv not in subtrahend
        assert iv in minuend

    difference = minuend.difference(subtrahend)
    difference.verify()

    for iv in difference:
        assert iv not in subtrahend
        assert iv in minuend
        assert iv in expected_difference

    assert difference == expected_difference


def test_difference_operator():
    minuend = IntervalTree.from_tuples(data.ivs1.data)
    assert isinstance(minuend, IntervalTree)
    subtrahend = minuend.copy()
    expected_difference = IntervalTree([subtrahend.pop()])
    expected_difference.add(subtrahend.pop())

    minuend.verify()
    subtrahend.verify()
    expected_difference.verify()

    assert len(expected_difference) == len(minuend) - len(subtrahend)

    for iv in expected_difference:
        assert iv not in subtrahend
        assert iv in minuend

    difference = minuend - subtrahend
    difference.verify()

    for iv in difference:
        assert iv not in subtrahend
        assert iv in minuend
        assert iv in expected_difference

    assert difference == expected_difference


def test_intersection():
    a = IntervalTree.from_tuples(data.ivs1.data)
    b = IntervalTree.from_tuples(data.ivs2.data)
    e = IntervalTree()

    # intersections with e
    assert a.intersection(e) == e
    assert b.intersection(e) == e
    assert e.intersection(e) == e

    # intersections with self
    assert a.intersection(a) == a
    assert b.intersection(b) == b

    # commutativity resulting in empty
    ab = a.intersection(b)
    ba = b.intersection(a)
    ab.verify()
    ba.verify()
    assert ab == ba
    assert len(ab) == 0  # no overlaps, so empty tree

    # commutativity on non-overlapping sets
    ab = a.union(b)
    ba = b.union(a)

    aba = ab.intersection(a)  # these should yield no change
    abb = ab.intersection(b)
    bab = ba.intersection(b)
    baa = ba.intersection(a)
    aba.verify()
    abb.verify()
    bab.verify()
    baa.verify()
    assert aba == a
    assert abb == b
    assert bab == b
    assert baa == a

    # commutativity with overlapping sets
    c = IntervalTree.from_tuples(data.ivs3.data)
    bc = b.intersection(c)
    cb = c.intersection(b)
    bc.verify()
    cb.verify()
    assert bc == cb
    assert len(bc) < len(b)
    assert len(bc) < len(c)
    assert len(bc) > 0

    assert b.containsi(13, 23)
    assert c.containsi(13, 23)
    assert bc.containsi(13, 23)

    assert not b.containsi(819, 828)
    assert not c.containsi(0, 1)
    assert not bc.containsi(819, 820)
    assert not bc.containsi(0, 1)


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
