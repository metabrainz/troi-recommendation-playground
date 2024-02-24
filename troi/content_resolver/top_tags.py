import logging

from troi.content_resolver.model.database import db

logger = logging.getLogger(__name__)


class TopTags:
    '''
       Class to fetch top tags
    '''

    def get_top_tags(self, limit=50):
        """
        """

        query = """SELECT tag.name
                        , COUNT(tag.id) AS cnt
                     FROM tag
                     JOIN recording_tag
                       ON recording_tag.tag_id = tag.id
                     JOIN recording
                       ON recording_tag.recording_id = recording.id
                 GROUP BY tag.name
                 ORDER BY cnt DESC
                    LIMIT ?"""

        cursor = db.execute_sql(query, (limit,))

        top_tags = []
        for rec in cursor.fetchall():
            top_tags.append({"tag": rec[0], "count": rec[1]})

        return top_tags

    def print_top_tags(self, limit=50):

        top_tags = self.get_top_tags(limit)
        for tt in top_tags:
            logger.info("%-40s %d" % (tt["tag"], tt["count"]))
        logger.info("")

    def print_top_tags_tightly(self, limit=250):

        top_tags = self.get_top_tags(limit)

        logger.info("; ".join(["%s %s" % (tt["tag"], tt["count"]) for tt in top_tags]))
