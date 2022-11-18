#!/usr/bin/env python3

days_and_thresholds = [(1460, 75), (730, 50)]
sessions = [300, 400, 500, 600]
contributions = [5,9,13,17]
limits = [50]

# --days 730 --threshold 5 --limit 200 --session 400

for day, threshold in days_and_thresholds:
    for session in sessions:
        for contribution in contributions:
            for limit in limits:
                print(f"docker exec -it listenbrainz-spark-reader-prod python manage.py spark request_similar_recordings --days {day} --session {session} --threshold {threshold} --contribution {contribution} --limit {limit} --filter-artist-credit True")
