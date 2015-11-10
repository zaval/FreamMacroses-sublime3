import sublime, sublime_plugin
import re
from urllib.parse import unquote


class Fream_macrosesCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		sel = self.view.sel()

		if not sel:
			return

		macro = self.view.substr(sel[0])
		replace = self.process_request(macro)

		if replace:
			if isinstance(replace, tuple):
				text, cursor = replace
			else:
				text = replace
				cursor = 0

			self.view.erase(edit, sel[0])
			self.view.insert(edit, sel[0].a, text)
			end_cursor = self.view.sel()[0].b
			if cursor > 0:
				print(self.view.sel()[0].b)
				self.view.sel().clear()
				self.view.sel().add(sublime.Region(end_cursor - len(text) + cursor))
			if cursor < 0:
				self.view.sel().clear()
				self.view.sel().add(sublime.Region(end_cursor + cursor))

	def process_request(self, text):

		if re.match(r'^\s*http\s\S+$', text):
			res = re.search(r'^(\s*)http\s+(\S+)$', text)
			if not res:
				return

			if res.group(2).startswith('http'):
				result = res.group(1) + "page = self.http.get('" + res.group(2) + "')"
			else:
				result = res.group(1) + "page = self.http.get(" + res.group(2) + ")"

			return result

		elif re.match(r'^\s*http\s\S+\s+\S+$', text):
			res = re.search(r'^(\s*)http\s+(\S+)\s+(\S+)$', text)
			if not res:
				return

			ajax = ''
			if res.group(3) == 'ajax':
				ajax = '.ajax()'

			if res.group(2).startswith('http'):
				result = res.group(1) + "page = self.http" + ajax + ".post('" + res.group(2) + "', data)"
			else:
				result = res.group(1) + "page = self.http" + ajax + ".post(" + res.group(2) + ", data)"

			return result

		elif re.match(r'^\s*pd\s+.+$', text):
			res = re.search(r'(\s*)pd\s+(.+)$', text)
			if not res:
				return

			elems = [v for v in res.group(2).split('&') if v.strip()]
			result = res.group(1) + 'data = {\n'

			for elem in elems:

				try:
					key, val = elem.split('=')
				except:
					key = elem
					val = ''

				key = unquote(key)
				val = unquote(val)
				result += res.group(1) + "\t'{}': '{}',\n".format(key, val)

			result += res.group(1) + '}'
			return result

		elif re.match(r'^f$', text):
			return '.format()', -1

		elif re.match(r'^b$', text):
			return '<b>{}</b>'

		elif re.match(r'^i$', text):
			return '<i>{}</i>'

		elif re.match(r'^\s*(?:parse|parse_all)\s\S+', text):
			res = re.search(r'^(\s*)(parse|parse_all)\s+(\S+)$', text)
			if not res:
				return

			result = '{0}{2} = hlp.{1}(r\'([^"]+)\', page)\n{0}if not {2}:\n{0}\tself.log("не смогли достать {2}", "!")\n{0}\treturn False\n{0}else:\n{0}\tself.log("достали {2}: %s" % {2}, "+")'.format(*list(res.groups()))
			cursor = result.find("r'([^\"]+)") + 2
			return result, cursor

		elif re.match(r'^\s*l\s.+?\s*(?:\+|\*|\-|~|!|)', text):
			res = re.search(r'^(\s*)l\s(.+?)\s*(\+|\*|\-|~|!*)$', text)
			if not res:
				return

			args = [
				res.group(1),
				"'" if re.sub(r'[a-z0-9_ ]+', '', res.group(2)) else "",
				res.group(2),
				'' if not res.group(3) else ", '{}'".format(res.group(3))
			]

			result = "{0}self.log({1}{2}{1}{3})".format(*args)
			return result

		elif re.match(r'^\s*cnf\s+\S+\s*\S*', text):
			res = re.search(r'^(\s*)cnf\s+(\S+)\s*(\S*)', text)
			if not res:
				return

			result = "{0}self.cnf.get{2}('{1}')".format(*list(res.groups()))
			return result

		elif re.match(r'^\s*cnt\s+\S+', text):
			res = re.search(r'^(\s*)cnt\s+(\S+)', text)
			if not res:
				return

			result = "{0}self.hlp.cnt('{1}')".format(*list(res.groups()))
			return result

		elif re.match(r'^\s*slp\s+\S+', text):
			res = re.search(r'^(\s*)slp\s+(\S+)', text)
			if not res:
				return

			if re.sub(r'\d+', '', res.group(2)):
				result = "{0}self.hlp.slp('{1}', log=self.log)".format(*list(res.groups()))
			else:
				result = "{0}self.hlp.slp({1}, log=self.log)".format(*list(res.groups()))
			return result

		elif re.match(r'^\s*data\s+\S+$', text):
			res = re.search(r'^\s*data\s+(\S+)$', text)
			if not res:
				return
			result = "self.data['" + res.group(1) + "']"
			return result

		elif re.match(r'^\s*ac$', text):
			res = re.search(r'^(\s*)ac', text)
			return res.group(1) + "actext = self.ac.captcha(captcha_url)\n" + res.group(1) + "if self.ac.error:\n" + res.group(1) + "\tself.log('ошибка разгадки: {}'.format(self.ac.last_error), '!')\n" + res.group(1) + "\treturn False\n" + res.group(1) + "else:\n" + res.group(1) + "\tself.log('разгадали: ' + actext, '+')  # self.ac.recaptcha_challenge # self.ac.bad()"

		elif re.match(r'^\s*pdf\s', text):
			res = re.search(r'^(\s*)pdf\s+([\s\S]+)', text)
			content = res.group(2)

			items = re.findall(r'form\-data;\s+name="([^"]+)"\n\n(.*)', content)
			result = res.group(1) + "data = {\n"
			for item in items:
				result += res.group(1) + "\t'{}': '{}',\n".format(*item)
			items = re.findall(r'form\-data;\s+name="([^"]+)"\s*;\s*filename="', content)
			for item in items:
				result += res.group(1) + "\t'%s': '@{}',\n" % item
			result += res.group(1) + '}\n'
			return result
