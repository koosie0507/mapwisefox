from pydantic.dataclasses import dataclass


@dataclass
class Point:
    x: float = 0.0
    y: float = 0.0


@dataclass
class Size:
    width: float = 0.0
    height: float = 0.0


@dataclass
class Rect:
    start: Point
    end: Point

    def __post_init__(self):
        self.__size = Size(
            abs(self.end.x - self.start.x), abs(self.end.y - self.start.y)
        )
        self.__center = Point(
            x=((self.start.x + self.end.x) / 2),
            y=((self.start.y + self.end.y) / 2),
        )

    def includes(self, other: "Rect") -> bool:
        return (self.start.x <= other.start.x and self.start.y <= other.start.y) and (
            self.end.x >= other.end.x and self.end.y >= other.end.y
        )

    def is_included(self, other: "Rect") -> bool:
        return other.includes(self)

    def _compute_intersection_points(self, other: "Rect") -> tuple[Point, Point]:
        int_start = Point(
            max(self.start.x, other.start.x), max(self.start.y, other.start.y)
        )
        int_end = Point(min(self.end.x, other.end.x), min(self.end.y, other.end.y))
        return int_start, int_end

    def intersects(self, other: "Rect") -> bool:
        s, e = self._compute_intersection_points(other)
        return s.x <= e.x and s.y <= e.y

    def intersection(self, other: "Rect") -> "Rect":
        s, e = self._compute_intersection_points(other)
        return Rect(start=s, end=e)

    def union(self, other: "Rect") -> "Rect":
        s = Point(min(self.start.x, other.start.x), min(self.start.y, other.start.y))
        e = Point(max(self.end.x, other.end.x), max(self.end.y, other.end.y))
        return Rect(start=s, end=e)

    @property
    def size(self) -> Size:
        return self.__size

    @property
    def height(self) -> float:
        return abs(self.end.y - self.start.y)

    @property
    def center(self) -> Point:
        return self.__center

    def vertical_norm(self, relative_height: float) -> float:
        if self.center.y > relative_height:
            return 1.0
        if self.center.y < 0:
            return 0.0
        return round(self.center.y / relative_height, 4)

    def __or__(self, other: "Rect") -> "Rect":
        assert isinstance(other, Rect), "expected another Rect instance"
        return self.union(other)

    def __and__(self, other: "Rect") -> "Rect":
        assert isinstance(other, Rect), "expected another Rect instance"
        return self.intersection(other)

    def scale(self, sx: float, sy: float) -> "Rect":
        return Rect(
            start=Point(self.start.x * sx, self.start.y * sy),
            end=Point(self.end.x * sx, self.end.y * sy),
        )


@dataclass
class TextItem:
    text: str
    font_size: float
    font_dict: dict | None
    bounds: Rect


@dataclass
class LayoutBox:
    type: str
    bounds: Rect
