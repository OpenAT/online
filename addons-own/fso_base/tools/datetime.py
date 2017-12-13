# -*- coding: utf-8 -*-

import datetime
import pytz


def naive_to_timezone(naive=False, naive_tz=pytz.UTC, naive_dst=False, target_tz=False):
    """
    Converts a naive datetime to a timezone aware datetime.

    Retrurns 'now' in the UTC timezone if no options are given

    Optionally:
    If set target_timezone will convert the timezone aware datetime object to the desired target timezone

    :param naive: Naive datetime without tzinfo
    :param naive_tz: Timezone of the naive datetime
    :param naive_dst: Set if the naive datetime given is daylight saving aware or not?
        e.g.: If the naive_datetime is in Sommerzeit or Winterzeit (just as you speak it) it should be set to True.
        Possible values are 'True', 'False' or 'None' ('None' will raise exceptions if you try to build ambiguous or
        non-existent times)
    :param target_tz: Convert the datetime to the target timezone
    :return (datetime): Timezone Object
    """
    if not naive:
        naive = datetime.datetime.now()

    # https://stackoverflow.com/questions/43324731/timezone-in-odoo-9
    # ATTENTION: Do NOT use 'tzinfo' but 'localize' instead or you will get unexpected behaviour because of
    #            Timeshifts in the pytz lib! See: http://pytz.sourceforge.net/
    # https://gist.github.com/michaelkarrer81/d020b7400775d5e7a71ef4053cfb4ae4
    res = naive_tz.localize(naive, is_dst=naive_dst)

    if target_tz:
        res = res.astimezone(target_tz)

    return res
