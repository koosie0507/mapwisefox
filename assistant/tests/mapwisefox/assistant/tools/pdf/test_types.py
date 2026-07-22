import pytest

from mapwisefox.assistant.tools.pdf._types import LayoutBox, Point, Rect, Size


def test_point_and_size_have_compact_representations():
    assert repr(Point(1.234, 5.678)) == "(1.23;5.68)"
    assert repr(Size(10.123, 20.456)) == "10.12x20.46"


def test_rect_computes_size_area_center_and_containment():
    rect = Rect(Point(0, 0), Point(10, 20))
    inner = Rect(Point(2, 3), Point(4, 5))

    assert rect.size == Size(10, 20)
    assert rect.area == 200
    assert rect.center == Point(5, 10)
    assert rect.includes(inner)
    assert inner.is_included(rect)


def test_rect_intersection_overlap_and_union():
    left = Rect(Point(0, 0), Point(10, 10))
    right = Rect(Point(5, 5), Point(15, 15))
    separate = Rect(Point(20, 20), Point(30, 30))

    assert left.intersects(right)
    assert left.intersection(right).area == 25
    assert left.overlap_area(right) == 25
    assert left.overlap_ratio(right) == 0.25
    assert not left.intersects(separate)
    assert left.overlap_area(separate) == 0
    assert (left | right).area == 225
    assert (left & right).area == 25


def test_rect_handles_zero_area_and_vertical_normalization():
    rect = Rect(Point(0, 0), Point(0, 0))

    assert rect.overlap_ratio(rect) == 0
    assert rect.vertical_norm(10) == 0
    assert Rect(Point(0, 30), Point(0, 40)).vertical_norm(10) == 1
    assert Rect(Point(0, -30), Point(0, -20)).vertical_norm(10) == 0


def test_rect_scale_and_type_assertions():
    rect = Rect(Point(1, 2), Point(3, 4))

    assert rect.scale(2, 3).end == Point(6, 12)
    with pytest.raises(AssertionError):
        rect | "not a rect"


def test_layout_box_ensures_unique_types_and_unions_bounds():
    first = LayoutBox(["text"], Rect(Point(0, 0), Point(2, 2)))
    second = LayoutBox(["title"], Rect(Point(1, 1), Point(3, 3)))

    first.ensure_type("text").ensure_type("list")
    union = first.union(second)

    assert first.types == ["text", "list"]
    assert union.types == ["text", "list", "title"]
    assert union.bounds.area == 9
    assert union.scale(2, 2).bounds.area == 36
