from typing import Iterable


def has_observation(record: dict, observations: Iterable) -> bool:
    for observation in observations:
        if observation.employer is not None:
            if record["employer"]["id"] == observation.employer.id and observation.calendar_day_id == record["daily_id"]:
                return True
        else:
            if record["person"]["id"] == observation.person.id and observation.calendar_day_id == record["daily_id"]:
                return True

        
    return False