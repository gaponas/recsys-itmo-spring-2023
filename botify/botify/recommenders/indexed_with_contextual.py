import random
from .contextual import Contextual
from .recommender import Recommender


class IndexedAndContextual(Recommender):
    def __init__(self, tracks_redis, recommendations_redis, catalog):
        self.recommendations_redis = recommendations_redis
        self.tracks_redis_size = tracks_redis.dbsize()
        self.fallback = Contextual(tracks_redis, catalog)
        self.catalog = catalog

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:

        recommendations = self.recommendations_redis.get(user)
        if recommendations is not None:
            shuffled = list(self.catalog.from_bytes(recommendations))
            random.shuffle(shuffled)
            return shuffled[0]
        else:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)
