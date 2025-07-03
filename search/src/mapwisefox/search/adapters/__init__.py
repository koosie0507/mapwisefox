from ._acm import ACMAdapter
from ._base import QueryBuilderAdapter
from ._expr_tree import ExprTreeAdapter
from ._flat_output import FlatOutputAdapter
from ._science_direct import ScienceDirectAdapter
from ._scopus import ScopusAdapter
from ._springer import SpringerAdapter
from ._xplore import XploreAdapter
from ._wos import WebOfScienceAdapter

__all__ = [
    "ACMAdapter",
    "QueryBuilderAdapter",
    "ExprTreeAdapter",
    "FlatOutputAdapter",
    "ScienceDirectAdapter",
    "ScopusAdapter",
    "SpringerAdapter",
    "XploreAdapter",
    "WebOfScienceAdapter",
]
