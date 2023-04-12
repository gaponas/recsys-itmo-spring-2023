from .random import Random
from .recommender import Recommender
import random


class ContextualIndexed(Recommender):

    def __init__(self, tracks_redis, recommendations_redis, top_tracks, catalog):
        self.tracks_redis = tracks_redis
        self.top_tracks = top_tracks
        self.recommendations_redis = recommendations_redis
        self.fallback = Random(tracks_redis)
        self.catalog = catalog
        self.users_history = {}

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        u_hist = set()
        if user in self.users_history:
            u_hist = self.users_history[user]
        if len(u_hist) == self.tracks_redis.dbsize():
            u_hist = set()

        if prev_track_time < 0.7:
            return self.indexed_next(user, prev_track, prev_track_time, u_hist)
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.catalog.from_bytes(previous_track)
        recommendations = previous_track.recommendations
        if not recommendations:
            return self.topPop_next(user, prev_track, prev_track_time)

        shuffled = list(set(recommendations) - u_hist)
        if len(shuffled) != 0:
            random.shuffle(shuffled)
            return shuffled[0]
        return self.indexed_next(user, prev_track, prev_track_time, u_hist)


    def indexed_next(self, user: int, prev_track: int, prev_track_time: float, user_history):
        recommendations = self.recommendations_redis.get(user)
        if recommendations is not None:
            recs = list(self.catalog.from_bytes(recommendations))
            shuffled = list(set(recs) - user_history)
            if len(shuffled) != 0:
                random.shuffle(shuffled)
                res = shuffled[0]
                user_history.add(res)
                self.users_history[user] = user_history
                return res
        return self.topPop_next(user, prev_track, prev_track_time, user_history)


    def topPop_next(self, user: int, prev_track: int, prev_track_time: float, user_history):
        if self.top_tracks:
            shuffled = list(set(self.top_tracks)-user_history)
            if len(shuffled) != 0:
                random.shuffle(shuffled)
                res = shuffled[0]
                user_history.add(res)
                self.users_history[user] = user_history
                return res
        return self.fallback.recommend_next(user, prev_track, prev_track_time)

