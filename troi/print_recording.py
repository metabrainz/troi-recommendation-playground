def _print_recording(self, recording):
    from prettytable import PrettyTable
    import datetime
    
    table = PrettyTable()
    headers = ["Recording Name", "Artist Name", "MBID"]
    
    if self.print_year:
        headers.append("Year")
    if self.print_ranking:
        headers.append("Ranking")
    if self.print_listen_count:
        headers.append("Listen Count")
    if self.print_bpm:
        headers.append("BPM")
    if self.print_popularity:
        headers.append("Popularity")
    if self.print_latest_listened_at:
        headers.append("Last Listened")
    if self.print_moods:
        headers.append("Mood Aggressive")
    if self.print_genre:
        headers.append("Genres/Tags")
    
    table.field_names = headers
    row_data = []
    
    rec_name = recording.name if recording.name else f"[[ mbid:{recording.mbid} ]]"
    artist = recording.artist_credit.name if recording.artist_credit and recording.artist_credit.name else "[missing]"
    rec_mbid = recording.mbid[:5] if recording.mbid else "[[ ]]"
    
    row_data.extend([rec_name, artist, rec_mbid])
    
    if self.print_year:
        row_data.append(recording.year if recording.year is not None else "")
    if self.print_ranking:
        row_data.append(f"{recording.ranking:.3f}" if recording.ranking else "")
    if self.print_listen_count:
        row_data.append(recording.listenbrainz.get("listen_count", ""))
    if self.print_bpm:
        row_data.append(recording.acousticbrainz.get("bpm", ""))
    if self.print_popularity:
        row_data.append(f"{recording.musicbrainz.get('popularity', 0.0):.1f}")
    if self.print_latest_listened_at:
        if recording.listenbrainz.get("latest_listened_at") is None:
            row_data.append("never")
        else:
            now = datetime.datetime.now()
            td = now - recording.listenbrainz["latest_listened_at"]
            row_data.append(f"{td.days} days")
    if self.print_moods:
        mood_agg = recording.acousticbrainz.get("moods", {}).get("mood_aggressive", 0)
        row_data.append(f"{int(100 * mood_agg)}")
    if self.print_genre:
        genres = recording.musicbrainz.get("genres", [])
        tags = recording.musicbrainz.get("tags", [])
        row_data.append(", ".join(genres + tags))
    
    table.add_row(row_data)
    table.align = "l"
    logger.info("Recording Table:\n" + table.get_string())
    return table