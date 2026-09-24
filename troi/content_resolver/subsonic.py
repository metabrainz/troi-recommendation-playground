import datetime
import logging
import time
import re
import difflib
import libsonic
import musicbrainzngs

from libsonic.errors import DataNotFoundError
import peewee
from tqdm import tqdm

from troi.content_resolver.database import Database
from troi.content_resolver.model.database import db
from troi.content_resolver.model.recording import Recording, FileIdType
from troi.content_resolver.utils import bcolors

musicbrainzngs.set_useragent("TroiNextcloudResolver", "1.0", "https://github.com/metabrainz/troi")

logger = logging.getLogger("troi_subsonic_scan")

APP_LOG_LEVEL_NUM = 19
logging.addLevelName(APP_LOG_LEVEL_NUM, "NOTICE")

def applog(message, *args, **kwargs):
    logger._log(APP_LOG_LEVEL_NUM, message, args, **kwargs)


class FixedConnection(libsonic.Connection):
    def __init__(self, baseUrl, username, password, port=443, **kwargs):
        from urllib.parse import urlparse

        if not baseUrl.startswith("http://") and not baseUrl.startswith("https://"):
            baseUrl = f"https://{baseUrl}"

        parsed = urlparse(baseUrl)
        host_only = parsed.netloc.split(":")[0]
        clean_path = parsed.path.strip("/")

        kwargs["legacyAuth"] = True

        super().__init__(
            baseUrl=f"https://{host_only}",
            username=username,
            password=password,
            port=port,
            **kwargs
        )

        if clean_path:
            self._serverPath = f"/{clean_path}/rest"
        else:
            self._serverPath = "/rest"

    def _getApiUrl(self, action):
        return f"https://{self._hostname}{self._serverPath}/{action}.view"

    def _doInfoReq(self, req):
        return super()._doInfoReq(req)


class SubsonicDatabase(Database):
    BATCH_SIZE = 500
    FUZZY_THRESHOLD = 75

    def __init__(self, index_dir, config, quiet=False):
        self.config = config
        Database.__init__(self, index_dir, quiet)
        self.quiet = quiet
        self.mb_cache = {}

    def connect(self):
        if not self.config:
            logger.error("Missing credentials to connect to subsonic")
            return None

        logger.info("[ connect to subsonic ]")
        port = getattr(self.config, "SUBSONIC_PORT", 443) or 443

        return FixedConnection(
            baseUrl=self.config.SUBSONIC_HOST,
            username=self.config.SUBSONIC_USER,
            password=self.config.SUBSONIC_PASSWORD,
            port=port
        )

    def fetch_release_details_from_musicbrainz(self, album_mbid=None, artist=None, album_name=None):
        cache_key = album_mbid or f"{artist} - {album_name}".lower()
        if cache_key in self.mb_cache:
            return self.mb_cache[cache_key]

        try:
            time.sleep(0.5)
            target_release_id = album_mbid

            if not target_release_id and artist and album_name:
                result = musicbrainzngs.search_release_groups(artist=artist, release=album_name, limit=1)
                release_groups = result.get("release-group-list", [])
                if release_groups:
                    rg_id = release_groups[0]["id"]
                    rel_result = musicbrainzngs.search_releases(rgid=rg_id, limit=1)
                    releases = rel_result.get("release-list", [])
                    if releases:
                        target_release_id = releases[0]["id"]

            if target_release_id:
                rel_data = musicbrainzngs.get_release_by_id(target_release_id, includes=["recordings", "artist-credits"])
                rel = rel_data.get("release", {})
                
                rel_mbid = rel.get("id")
                artist_mbid = rel.get("artist-credit", [{}])[0].get("artist", {}).get("id")

                recordings_map = {}
                for medium in rel.get("medium-list", []):
                    for track in medium.get("track-list", []):
                        try:
                            t_num = int(track.get("number", 0))
                            r_mbid = track.get("recording", {}).get("id")
                            if t_num and r_mbid:
                                recordings_map[t_num] = r_mbid
                        except ValueError:
                            pass

                res = (rel_mbid, artist_mbid, recordings_map)
                self.mb_cache[cache_key] = res
                return res

        except Exception as e:
            logger.warning(f"MusicBrainz Lookup Fehler für {cache_key}: {e}")

        empty_res = (None, None, {})
        self.mb_cache[cache_key] = empty_res
        return empty_res

    def sync(self, incremental=True):
        """
        Startet den Sync-Prozess.
        :param incremental: Wenn True, werden nur neue Alben seit dem letzten Sync verarbeitet.
        """
        self.total = 0
        self.matched = 0
        self.error = 0

        self.run_sync(incremental=incremental)

        logger.info("Checked %s albums:" % self.total)
        logger.info("  %5d albums matched" % self.matched)
        logger.info("  %5d recordings with errors" % self.error)

    def run_sync(self, incremental=True):
        conn = self.connect()
        if not conn:
            return

        logger.info("[ load ALL albums from Subsonic ]")
        album_ids = set()
        all_albums = []
        offset = 0

        # 1. Alle Alben-Metadaten von Subsonic holen (geht sehr schnell)
        while True:
            results = conn.getAlbumList2(ltype="alphabeticalByArtist", size=self.BATCH_SIZE, offset=offset)
            batch = results.get("albumList2", {}).get("album", [])
            
            if not batch:
                break

            all_albums.extend(batch)
            offset += len(batch)
            if len(batch) < self.BATCH_SIZE:
                break

        logger.info(f"[ Subsonic meldet insgesamt {len(all_albums)} Alben ]")

        # 2. Filtern: Nur Alben behalten, die NOCH NICHT in steffen.db sind
        albums_to_process = []
        for album in all_albums:
            album_name = album.get("name")
            # Prüfen, ob Songs dieses Albums bereits in der lokalen SQLite-DB existieren
            exists = Recording.select().where(Recording.release_name == album_name).exists()
            if not exists:
                albums_to_process.append(album)

        if not albums_to_process:
            print("✨ Keine fehlenden Alben gefunden. Deine Datenbank ist wirklich zu 100% aktuell!")
            return

        print(f"🔄 {len(albums_to_process)} von {len(all_albums)} Alben fehlen noch in steffen.db. Starte Import...")

        if not self.quiet:
            pbar = tqdm(total=len(albums_to_process))

        # 3. Nur die tatsächlich fehlenden Alben verarbeiten (inkl. MBID-Lookups)
        for album in albums_to_process:
            album_info = conn.getAlbum(id=album["id"])
            raw_album_mbid = album_info.get("musicBrainzId", album.get("musicBrainzId"))
            
            album_mbid, artist_mbid, mb_tracks = self.fetch_release_details_from_musicbrainz(
                album_mbid=raw_album_mbid,
                artist=album.get("artist", ""),
                album_name=album.get("name", "")
            )

            if not album_mbid:
                if not self.quiet:
                    msg = "subsonic album '%s' by '%s' has no MBID" % (album["name"], album["artist"])
                    pbar.write(bcolors.FAIL + "FAIL " + bcolors.ENDC + msg)
                    applog("FAIL: " + msg)
                self.error += 1
                if not self.quiet:
                    pbar.update(1)
                continue

            for song in album_info["album"]["song"]:
                track_num = int(song.get("track", 1))
                
                song_mbid = song.get("musicBrainzId")
                if not song_mbid or song_mbid == album_mbid:
                    song_mbid = mb_tracks.get(track_num)

                clean_path = song.get("path", "").lstrip("/")

                self.add_subsonic({
                    "artist_name": song["artist"],
                    "release_name": song["album"],
                    "recording_name": song["title"],
                    "path": clean_path,  
                    "artist_mbid": artist_mbid or "00000000-0000-0000-0000-000000000000",
                    "release_mbid": album_mbid,
                    "recording_mbid": song_mbid,
                    "duration": song.get("duration", 0) * 1000,
                    "track_num": track_num,
                    "disc_num": song.get("discNumber", 1),
                    "subsonic_id": song["id"],
                    "mtime": datetime.datetime.now()
                })

            if not self.quiet:
                msg = "album %-50s %-50s" % (album["name"][:49], album["artist"][:49])
                pbar.write(bcolors.OKGREEN + "OK   " + bcolors.ENDC + msg)
                applog(msg)

            self.matched += 1
            self.total += 1
            if not self.quiet:
                pbar.update(1)

    def add_subsonic(self, mdata):
        with db.atomic():
            try:
                recording = Recording.select().where(Recording.file_id == mdata['subsonic_id']).get()
                recording.artist_name = mdata["artist_name"]
                recording.release_name = mdata["release_name"]
                recording.recording_name = mdata["recording_name"]
                recording.artist_mbid = mdata["artist_mbid"]
                recording.release_mbid = mdata["release_mbid"]
                recording.recording_mbid = mdata["recording_mbid"]
                recording.mtime = mdata["mtime"]
                recording.track_num = mdata["track_num"]
                recording.disc_num = mdata["disc_num"]
                recording.path = mdata["path"]
                recording.save()
            except peewee.DoesNotExist:
                recording = Recording.create(
                    file_id=mdata["subsonic_id"],
                    file_id_type=FileIdType(FileIdType.SUBSONIC_ID),
                    artist_name=mdata["artist_name"],
                    release_name=mdata["release_name"],
                    recording_name=mdata["recording_name"],
                    artist_mbid=mdata["artist_mbid"],
                    release_mbid=mdata["release_mbid"],
                    recording_mbid=mdata["recording_mbid"],
                    mtime=mdata["mtime"],
                    duration=mdata["duration"],
                    track_num=mdata["track_num"],
                    disc_num=mdata["disc_num"],
                    path=mdata["path"]
                )
                recording.save()

    # --- INTELLIGENTE FUZZY MATCHING LOGIK (1:1 PORTIERT AUS BASH) ---
    @staticmethod
    def _clean_string(s):
        """Säubert Sonderzeichen & typische Klammerzusätze (Remaster, Live, Version, etc.)"""
        if not s:
            return ""
        s = s.replace("’", "'").replace("‘", "'").replace("`", "'").replace("´", "'")
        s = re.sub(
            r"\s*[\(\[][^\]\)]*(remaster|live|cover|edit|version|explicit|feat|ft)[^\]\)]*[\)\]]",
            "",
            s,
            flags=re.IGNORECASE,
        )
        return " ".join(s.lower().split())

    @staticmethod
    def _similarity(s1, s2):
        if not s1 or not s2:
            return 0
        return int(difflib.SequenceMatcher(None, s1, s2).ratio() * 100)

    def _find_best_match(self, songs, target_title, target_artist):
        best_id = None
        best_score = 0
        best_name = ""

        clean_req_title = self._clean_string(target_title)
        clean_req_artist = self._clean_string(target_artist)

        for song in songs:
            song_id = song.get("id") if isinstance(song, dict) else getattr(song, "id", None)
            title = song.get("title", "") if isinstance(song, dict) else getattr(song, "title", "")
            artist = song.get("artist", "") if isinstance(song, dict) else getattr(song, "artist", "")

            if not song_id:
                continue

            title_score = self._similarity(self._clean_string(title), clean_req_title)

            if target_artist:
                artist_score = self._similarity(self._clean_string(artist), clean_req_artist)
                # Artist-Veto: Wenn Interpret-Match unter 50%, verwirf den Song!
                if artist_score < 50:
                    total_score = 0
                else:
                    total_score = int((title_score * 0.5) + (artist_score * 0.5))
            else:
                total_score = title_score

            if total_score > best_score:
                best_score = total_score
                best_id = song_id
                best_name = f"{title} - {artist}"

        if best_id and best_score >= self.FUZZY_THRESHOLD:
            return "FOUND", best_id, best_score
        elif best_id:
            return "LOW_SCORE", best_name, best_score
        return "NOT_FOUND", "Keine Treffer", 0

    def _smart_search_song(self, conn, title, artist):
        """Setzt die 4-Stufen-Suchstrategie aus dem funktionierenden Shell-Skript um"""
        
        # --- 1. VERSUCH: Standard-Suche (Nur Titel) ---
        try:
            res = conn.search3(query=title, songCount=30)
            songs = res.get("searchResult3", {}).get("song", [])
        except Exception:
            songs = []

        status, val1, val2 = self._find_best_match(songs, title, artist)

        # --- 2. VERSUCH: Sonderzeichen-Fallback ---
        if status != "FOUND":
            clean_query = re.sub(r"['’‘\`´.,!?]", "", title)
            if clean_query != title:
                try:
                    res = conn.search3(query=clean_query, songCount=30)
                    songs = res.get("searchResult3", {}).get("song", [])
                    status, val1, val2 = self._find_best_match(songs, title, artist)
                except Exception:
                    pass

        # --- 3. VERSUCH: Scharfschützen-Suche (Artist + Hauptwort) ---
        if status != "FOUND" and artist:
            words = [w for w in re.sub(r"['’‘\`´]", "", title).split() if len(w) >= 4]
            core_word = words[0] if words else title.split()[0] if title.split() else ""
            if core_word:
                try:
                    res = conn.search3(query=f"{artist} {core_word}".strip(), songCount=40)
                    songs = res.get("searchResult3", {}).get("song", [])
                    status, val1, val2 = self._find_best_match(songs, title, artist)
                except Exception:
                    pass

        # --- 4. VERSUCH: Breiter Artist-Fallback ---
        if status != "FOUND" and artist:
            try:
                res = conn.search3(query=artist, songCount=120)
                songs = res.get("searchResult3", {}).get("song", [])
                status, val1, val2 = self._find_best_match(songs, title, artist)
            except Exception:
                pass

        return status, val1, val2

    def upload_playlist(self, playlist_element, playlist_id=None):
        conn = self.connect()
        if not conn:
            logger.error("Keine Verbindung zu Subsonic möglich.")
            return

        # 1. Troi-Playlist aus dem Pipeline-Element extrahieren
        troi_playlists = getattr(playlist_element, "playlists", [])
        if not troi_playlists:
            print("⚠️ Keine Playlists im Troi-Element gefunden.")
            return

        pl = troi_playlists[0]
        recordings = getattr(pl, "recordings", [])

        if not recordings:
            print("⚠️ Keine Tracks in pl.recordings gefunden.")
            return

        playlist_title = getattr(pl, "name", "Troi LB Radio Playlist")
        print(f"\nStarte Sync für Playlist '{playlist_title}' mit {len(recordings)} Tracks...")

        matched_song_ids = []

        # 2. Iteration über die Troi Recordings (IDs nur SAMMELN)
        for idx, rec in enumerate(recordings, 1):
            title = (
                getattr(rec, "track_name", None) or 
                getattr(rec, "recording_name", None) or 
                getattr(rec, "name", None) or 
                getattr(rec, "title", None)
            )

            artist = (
                getattr(rec, "artist_credit", None) or 
                getattr(rec, "artist_name", None) or 
                getattr(rec, "artist", None)
            )

            if artist and not isinstance(artist, str):
                artist = getattr(artist, "name", str(artist))

            if not title:
                print(f"[{idx}/{len(recordings)}] ⚠️ Songtitel konnte nicht gelesen werden.")
                continue

            artist_str = artist or ""
            print(f"[{idx}/{len(recordings)}] Suche Nextcloud: '{title}' (von '{artist_str}')... ", end="", flush=True)

            # Intelligente 4-Stufen-Suche ausführen
            status, match_val, score = self._smart_search_song(conn, title, artist_str)

            if status == "FOUND":
                matched_song_ids.append(str(match_val))
                print(f"✅ Gefunden! ({score}%) [ID: {match_val}]")
            elif status == "LOW_SCORE":
                print(f"⚠️ Nicht eindeutig (Veto). Bester Treffer war '{match_val}' mit {score}%")
            else:
                print("❌ Nicht gefunden.")

            time.sleep(0.1)

        # 3. GESAMTE PLAYLIST AUF EINMAL ERSTELLEN ODER ERWEITERN
        if not matched_song_ids:
            print("\n⚠️ Keine passenden Songs in Nextcloud gefunden. Playlist wird nicht erstellt.")
            return

        print(f"\nErstelle/Aktualisiere Playlist '{playlist_title}' mit {len(matched_song_ids)} Songs in Nextcloud...")
        
        try:
            if playlist_id:
                # Falls eine explizite ID übergeben wurde: per updatePlaylist anhängen
                conn.updatePlaylist(playlistId=playlist_id, songIdsToAdd=matched_song_ids)
            else:
                # Playlist mit allen gesammelten Song-IDs auf einmal erstellen
                conn.createPlaylist(name=playlist_title, songIds=matched_song_ids)
            
            print(f"🎉 Erfolgreich! {len(matched_song_ids)} von {len(recordings)} Songs wurden zur Playlist hinzugefügt.")
        except Exception as e:
            print(f"❌ Fehler beim Befüllen der Subsonic-Playlist: {e}")
