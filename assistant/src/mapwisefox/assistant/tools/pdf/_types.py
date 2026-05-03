from pydantic.dataclasses import dataclass


@dataclass
class Point:
    x: float = 0.0
    y: float = 0.0

    def __repr__(self) -> str:
        return f"({round(self.x, 2)};{round(self.y, 2)})"


@dataclass
class Size:
    width: float = 0.0
    height: float = 0.0

    def __repr__(self) -> str:
        return f"{round(self.width, 2)}x{round(self.height, 2)}"


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
        self.__area = self.__size.width * self.__size.height

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

    def overlap_area(self, other: "Rect") -> float:
        if not self.intersects(other):
            return 0.0
        return self.intersection(other).area

    def overlap_ratio(self, other: "Rect") -> float:
        min_area = min(self.area, other.area)
        if min_area == 0:
            return 0
        return self.overlap_area(other) / min_area

    def union(self, other: "Rect") -> "Rect":
        s = Point(min(self.start.x, other.start.x), min(self.start.y, other.start.y))
        e = Point(max(self.end.x, other.end.x), max(self.end.y, other.end.y))
        return Rect(start=s, end=e)

    @property
    def size(self) -> Size:
        return self.__size

    @property
    def area(self) -> float:
        return self.__area

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

    def __repr__(self) -> str:
        return f"{{{repr(self.start)}->{repr(self.end)};{repr(self.size)}}}"


@dataclass
class TextItem:
    text: str
    font_size: float
    font_dict: dict | None
    bounds: Rect


@dataclass
class LayoutBox:
    types: list[str]
    bounds: Rect

    def ensure_type(self, layout_type: str) -> "LayoutBox":
        if self.types is None:
            self.types = []
        if layout_type not in self.types:
            self.types.append(layout_type)
        return self

    def union(self, other: "LayoutBox") -> "LayoutBox":
        result = LayoutBox(types=[], bounds=self.bounds.union(other.bounds))
        for layout_type in self.types + other.types:
            result.ensure_type(layout_type)
        return result

    def scale(self, sx: float = 1.0, sy: float = 1.0) -> "LayoutBox":
        return LayoutBox(types=self.types, bounds=self.bounds.scale(sx, sy))
