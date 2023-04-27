from dataclasses import dataclass, field
from datetime import datetime

current_day = datetime.today()
current_year = datetime.today().year


@dataclass
class Movie:
    _id: str  # field(init=False) to prevent it from being passed as an argument to the class constructor
    title: str
    director: str
    year: int
    cast: list[str] = field(default_factory=list)
    series: list[str] = field(default_factory=list)
    last_watched: datetime = None
    rating: int = 0
    tags: list[str] = field(default_factory=list)
    description: str = None
    video_link: str = None

    # def __post_init__(self):
    #     """
    #     :return: method is called after the class is instantiated, and it generates a new unique ID using the
    #     uuid.uuid4().hex method and assigns it to the _id attribute.
    #     """
    #     self._id = uuid.uuid4().hex
    @property
    def id(self):
        return self._id


@dataclass
class User:
    _id: str
    name: str
    email: str
    password: str
    confirmed: bool = False
    movies: list[str] = field(default_factory=list)

    @property
    def id(self):
        return self._id
