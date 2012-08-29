# ZLib license:
# This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.
import time
import datetime

class DateTimeParser(object):
	"""This is originally from: http://www.logarithmic.net/pfh-files/blog/01162445830/parse_datetime.py, I made some modifications to allow for parsing of date and/or time, and added some format"""
	time_formats = ['%H:%M', '%I:%M%p', '%H', '%I%p']
	date_formats_with_year = ['%d %m %Y', '%Y %m %d', '%d %B %Y', '%B %d %Y', '%d %b %Y', '%b %d %Y', '%d %m %y', '%y %m %d', '%d %B %y', '%B %d %y', '%d %b %y', '%b %d %y']
	date_formats_without_year = ['%d %B', '%B %d', '%d %b', '%b %d']

	def parseTime(self, input):
		if (not input) or (len(input) == 0):
			return datetime.time(0, 0)
		
		input = str.rstrip(input)
		input = str.replace(input, 'h',':')

		for format in self.time_formats:
			try:
				result = time.strptime(input, format)
				return datetime.time(result.tm_hour, result.tm_min)
			except ValueError:
				pass

		return None

	def parseDate(self, input):
		if (not input) or (len(input) == 0):
			return datetime.date.today()
		
		input = str.rstrip(input)

		input = str.replace(input, '/',' ')
		input = str.replace(input, '-',' ')
		input = str.replace(input, ',',' ')

		for format in self.date_formats_with_year:
			try:
				result = time.strptime(input, format)
				return datetime.date(result.tm_year, result.tm_mon, result.tm_mday)
			except ValueError:
				pass

		for format in self.date_formats_without_year:
			try:
				result = time.strptime(input, format)
				year = datetime.date.today().year
				return datetime.date(year, result.tm_mon, result.tm_mday)
			except ValueError:
				pass

		return None

	def parseDateTime(self, input):
		if (input == None):
			return int(time.time())

		hasBoth = (input.find('@') > -1)

		day = input
		when = input
		if (hasBoth):
			temp = str.split(input, '@')
			day = temp[0]
			when = temp[1]

		day = self.parseDate(str(day))
		when = self.parseTime(str(when))
		if (hasBoth):
			if (day == None) or (when == None):
				return None
		else:
			if (day == None):
				day = datetime.date.today()
			else:
				when = datetime.time(0, 0)

		if (hasBoth) and ((day == None) or (when == None)):
			return None

		dt = datetime.datetime(day.year, day.month, day.day, when.hour, when.minute, when.second)
		result = int(time.mktime(dt.timetuple()))

		return result