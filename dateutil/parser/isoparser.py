# -*- coding: utf-8 -*-
"""
This module offers a parser for ISO-8601 strings

It is intended to support all valid date, time and datetime formats per the
ISO-8601 specification, with a stricter mode for the most common subset.
"""
from datetime import datetime, timedelta, time, date
import calendar
from dateutil import tz

import re

__all__ = ["isoparse", "Isoparser"]

class Isoparser(object):
    def __init__(self, sep='T', default_year=None):
        """
        :param sep:
            A single character that separates date and time portions

        :param default_year:
            The default year to be used as the basis for parsing the uncommon
            no-year date formats.
        """
        if len(sep) != 1:
            raise ValueError('Separator must be a single character')

        self._sep = sep
        if default_year is not None:
            if not 1 <= default_year <= 9999:
                raise ValueError('Year must be in [1, 9999]')

            self._default_year = default_year
        else:
            self._default_year = datetime.now().year

    def isoparse(self, dt_str, common_only=False):
        """
        Parse an ISO-8601 datetime string into a :class:`datetime.datetime`.

        An ISO-8601 datetime string consists of a date portion, followed
        optionally by a time portion - the date and time portions are separated
        by a single character separator, which is ``T`` in the official
        standard.

        Supported date formats are:

        Common:

        - ``YYYY``
        - ``YYYY-MM`` or ``YYYYMM``
        - ``YYYY-MM-DD`` or `YYYYMMDD``

        Uncommon:

        - ``--MM-DD`` or ``--MMDD`` - Year unspecified
        - ``YYYY-Www`` or ``YYYYWww`` - ISO week (day defaults to 0)
        - ``YYYY-Www-D`` or ``YYYYWwwD`` - ISO week and day

        The ISO week and day numbering follows the same logic as
        :func:`datetime.date.isocalendar`.

        Supported time formats are:

        - ``hh``
        - ``hh:mm`` or ``hhmm``
        - ``hh:mm:ss`` or `hhmmss``
        - ``hh:mm:ss.sss`` or ``hh:mm:ss.ssssss`` (3-6 sub-second digits)

        Midnight is a special case for `hh`, as the standard supports both
        00:00 and 24:00 as a representation.

        .. caution::

            Support for fractional components other than seconds is part of the
            ISO-8601 standard, but is not currently implemented in this parser.

        Supported time zone offset formats are:

        - `Z` (UTC)
        - `±HH:MM`
        - `±HHMM`
        - `±HH`

        Offsets will be represented as :class:`dateutil.tz.tzoffset` objects,
        with the exception of UTC, which will be represented as
        :class:`dateutil.tz.tzutc`. Time zone offsets equivalent to UTC (such
        as `+00:00`) will also be represented as :class:`dateutil.tz.tzutc`.

        :param dt_str:
            A string or stream containing only an ISO-8601 datetime string

        :param common_only:
            If true, parsing the uncommon formats will throw an error.

        :return:
            Returns a :class:`datetime.datetime` representing the string.
            Unspecified components default to their lowest value, with the
            exception of year, which will use the value passed to the
            ``default_year`` parameter of the method's bound
            :class:`Isoparser` instance. If that
            would produce an invalid date (e.g. ``'--02-29'`` parsed with a
            non-leap-year default date), the default will be the last leap
            year to occur before the default year.
        """
        dt_str = getattr(dt_str, 'read', lambda: dt_str)()

        if common_only:
            components, pos = self._parse_isodate_common(dt_str)
        else:
            components, pos = self._parse_isodate(dt_str)

        if len(dt_str) > pos:
            if dt_str[pos] == self._sep:
                components += self._parse_isotime(dt_str[pos + 1:])
            else:
                raise ValueError('String contains unknown ISO components')

        return datetime(*components)

    def parse_isodate(self, datestr):
        """
        Parse the date portion of an ISO string.

        :param datestr:
            The string portion of an ISO string, without a separator

        :return:
            Returns a :class:`datetime.date` object
        """
        components, pos = self._parse_isodate(datestr)
        return date(*components)

    @classmethod
    def parse_isotime(cls, timestr):
        """
        Parse the time portion of an ISO string.

        :param timestr:
            The time portion of an ISO string, without a separator

        :return:
            Returns a :class:`datetime.time` object
        """
        return time(*cls._parse_isotime(timestr))

    @classmethod
    def parse_tzstr(cls, tzstr, zero_as_utc=True):
        """
        Parse a valid ISO time zone string.

        See :func:`Isoparser.isoparse` for details on supported formats.

        :param tzstr:
            A string representing an ISO time zone offset

        :param zero_as_utc:
            Whether to return :class:`dateutil.tz.tzutc` for zero-offset zones

        :return:
            Returns :class:`dateutil.tz.tzoffset` for offsets and
            :class:`dateutil.tz.tzutc` for ``Z`` and (if ``zero_as_utc`` is
            specified) offsets equivalent to UTC.
        """
        if tzstr == 'Z':
            return tz.tzutc()

        if len(tzstr) not in {3, 5, 6}:
            raise ValueError('Time zone offset must be 1, 3, 5 or 6 characters')

        if tzstr[0] == '-':
            mult = -1
        elif tzstr[0] == '+':
            mult = 1
        else:
            raise ValueError('Time zone offset requires sign')

        hours = int(tzstr[1:3])
        if len(tzstr) == 3:
            minutes = 0
        else:
            minutes = int(tzstr[(4 if tzstr[3] == ':' else 3):])

        if zero_as_utc and hours == 0 and minutes == 0:
            return tz.tzutc()
        else:
            if minutes > 59:
                raise ValueError('Invalid minutes in time zone offset')

            if hours > 23:
                raise ValueError('Invalid hours in time zone offset')

            return tz.tzoffset(None, mult * timedelta(hours=hours,
                                                      minutes=minutes))

    def _parse_isodate(self, dt_str):
        try:
            return self._parse_isodate_common(dt_str)
        except ValueError:
            return self._parse_isodate_uncommon(dt_str)

    def _parse_isodate_common(self, dt_str):
        len_str = len(dt_str)
        components = [1, 1, 1]

        pos = 0
        if len_str < 4:
            raise ValueError('ISO string too short')

        # Year
        components[0] = int(dt_str[0:4])
        pos = 4
        if pos >= len_str:
            return components, pos

        has_sep = dt_str[pos] == '-'
        if has_sep:
            pos += 1

        # Month
        if len_str - pos < 2:
            raise ValueError('Invalid common month')

        components[1] = int(dt_str[pos:pos + 2])
        pos += 2

        if pos >= len_str:
            return components, pos

        if has_sep:
            if dt_str[pos] != '-':
                raise ValueError('Invalid separator in ISO string')
            pos += 1

        # Day
        if len_str - pos < 2:
            raise ValueError('Invalid common day')
        components[2] = int(dt_str[pos:pos + 2])
        return components, pos + 2

    def _parse_isodate_uncommon(self, dt_str):
        if dt_str[0:2] == '--':
            # --MM-DD or --MMDD
            month = int(dt_str[2:4])
            pos = 4 + (dt_str[4] == '-')
            day = int(dt_str[pos:pos + 2])
            year = self._default_year

            if month == 2 and day == 29:
                # Calcualtes the latest leap year
                year -= year % 4
                if (year % 400) and not (year % 100):
                    year -= 4

            return [year, month, day], pos + 2

        # All other uncommon ISO formats start with the year
        year = int(dt_str[0:4])

        pos = 4 + (dt_str[4] == '-')   # Skip '-' if it's there
        if dt_str[pos] == 'W':
            # YYYY-?Www-?D?
            pos += 1
            weekno = int(dt_str[pos:pos + 2])
            pos += 2

            dayno = 1
            if len(dt_str) > pos:
                if dt_str[pos] == '-':
                    # YYYY-W
                    if dt_str[4] != '-':
                        raise ValueError('Inconsistent use of dash separator')
                    pos += 1

                dayno = int(dt_str[pos])
                pos += 1

            base_date = self._calculate_weekdate(year, weekno, dayno)
        else:
            # YYYYDDD or YYYY-DDD
            ordinal_day = int(dt_str[pos:pos + 3])
            pos += 3

            if ordinal_day < 1 or ordinal_day > (365 + calendar.isleap(year)):
                raise ValueError('Invalid ordinal day' +
                                 ' {} for year {}'.format(ordinal_day, year))

            base_date = date(year, 1, 1) + timedelta(days=ordinal_day - 1)

        components = [base_date.year, base_date.month, base_date.day]
        return components, pos

    @classmethod
    def _calculate_weekdate(cls, year, week, day):
        """
        Calculate the day of corresponding to the ISO year-week-day calendar.

        This function is effectively the inverse of
        :func:`datetime.date.isocalendar`.

        :param year:
            The year in the ISO calendar

        :param week:
            The week in the ISO calendar - range is [1, 53]

        :param day:
            The day in the ISO calendar - range is [1 (MON), 7 (SUN)]

        :return:
            Returns a :class:`datetime.date`
        """
        if not 0 < week < 54:
            raise ValueError('Invalid week: {}'.format(week))

        if not 0 < day < 8:     # Range is 1-7
            raise ValueError('Invalid weekday: {}'.format(day))

        # Get week 1 for the specific year:
        jan_4 = date(year, 1, 4)   # Week 1 always has January 4th in it
        week_1 = jan_4 - timedelta(days=jan_4.isocalendar()[2] - 1)

        # Now add the specific number of weeks and days to get what we want
        week_offset = (week - 1) * 7 + (day - 1)
        return week_1 + timedelta(days=week_offset)

    _MICROSECOND_END_REGEX = re.compile('[-+Z]+')

    @classmethod
    def _parse_isotime(cls, timestr):
        len_str = len(timestr)
        components = [0, 0, 0, 0, None]
        pos = 0
        comp = -1

        has_sep = len_str >= 3 and timestr[2] == ':'

        while pos < len_str and comp < 5:
            comp += 1

            if timestr[pos] in '-+Z':
                # Detect time zone boundary
                components[-1] = cls.parse_tzstr(timestr[pos:])
                pos = len_str
                break

            if comp < 3:
                # Hour, minute, second
                components[comp] = int(timestr[pos:pos + 2])
                pos += 2
                if has_sep and pos < len_str and timestr[pos] == ':':
                    pos += 1

            if comp == 3:
                # Microsecond
                if timestr[pos] != '.':
                    continue

                pos += 1
                us_str = cls._MICROSECOND_END_REGEX.split(timestr[pos:pos + 6],
                                                          1)[0]

                components[comp] = int(us_str) * 10**(6 - len(us_str))
                pos += len(us_str)

        if pos < len_str:
            raise ValueError('Unused components in ISO string')

        if components[0] == 24:
            # Standard supports 00:00 and 24:00 as representations of midnight
            if any(component != 0 for component in components[1:4]):
                raise ValueError('Hour may only be 24 at 24:00:00.000')
            components[0] = 0

        return components


DEFAULT_ISOPARSER = Isoparser()
isoparse = DEFAULT_ISOPARSER.isoparse
