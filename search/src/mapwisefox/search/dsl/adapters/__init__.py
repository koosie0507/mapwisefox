from ._acm import AcmDSLAdapter
from ._base import DSLAdapter
from ._science_direct import ScienceDirectDSLAdapter
from ._scopus import ScopusDSLAdapter
from ._springer import SpringerDSLAdapter
from ._wos import WebOfScienceDSLAdapter

__all__ = [
    "DSLAdapter",
    "AcmDSLAdapter",
    "ScienceDirectDSLAdapter",
    "ScopusDSLAdapter",
    "SpringerDSLAdapter",
    "WebOfScienceDSLAdapter",
]
