Full list of values saved
Screenshot added to capture sources mentioned in the list: https://tlgrm.eu/channels/news

All the available fields are kept for messages.

```
    for message in messages:
        data.append({
            "id": message.id,
            "peer_id": str(message.peer_id),
            "date": message.date,
            "message": message.message,
            "out": message.out,
            "mentioned": message.mentioned,
            "media_unread": message.media_unread,
            "silent": message.silent,
            "post": message.post,
            "from_scheduled": message.from_scheduled,
            "legacy": message.legacy,
            "edit_hide": message.edit_hide,
            "pinned": message.pinned,
            "noforwards": message.noforwards,
            "invert_media": message.invert_media,
            "offline": message.offline,
            "video_processing_pending": message.video_processing_pending,
            "from_id": str(message.from_id),
            "from_boosts_applied": message.from_boosts_applied,
            "saved_peer_id": str(message.saved_peer_id),
            "fwd_from": str(message.fwd_from),
            "via_bot_id": message.via_bot_id,
            "via_business_bot_id": message.via_business_bot_id,
            "reply_to": str(message.reply_to),
            "media": str(message.media),
            "reply_markup": str(message.reply_markup),
            "entities": str(message.entities),
            "views": message.views,
            "forwards": message.forwards,
            "replies": str(message.replies),
            "edit_date": message.edit_date,
            "post_author": message.post_author,
            "grouped_id": message.grouped_id,
            "reactions": str(message.reactions),
            "restriction_reason": str(message.restriction_reason),
            "ttl_period": message.ttl_period,
            "quick_reply_shortcut_id": message.quick_reply_shortcut_id,
            "effect": message.effect,
            "factcheck": message.factcheck,
        })
```
