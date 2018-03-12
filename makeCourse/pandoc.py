import logging
import os
import pkg_resources
import re
import sys
import datetime
from makeCourse import *
from subprocess import Popen, PIPE

logger = logging.getLogger(__name__)

class PandocRunner:
	def run_pandoc(self, item, template_file=None,format='html'):
		outPath = os.path.join(self.config['build_dir'], item.out_file+'.'+format)
		if template_file is None:
			template_file = item.template_file
		template_file = os.path.join(self.config['themes_dir'], self.config['theme'], template_file)
		date = datetime.date.today()

		logger.info('   {src} => {dest}'.format(src=item.title, dest=outPath))

		cmd = [
			'pandoc', '-markdown', '-s', '--toc','--toc-depth=2', '--section-divs', '--listings',
			'--title-prefix={}'.format(self.config['title']), '--mathjax={}'.format(self.mathjax_url),  
			'--metadata=date:{}'.format(date), 
			'-V', 'web_dir={}'.format(self.config['web_dir']), 
			'--template', template_file, 
			'-o', outPath,
		]
		content = item.markdown(pdf=format=='pdf')

		proc = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)

		try:
			outs, errs = proc.communicate(content)
		except:
			proc.kill()
			outs, errs = proc.communicate()

		if outs:
			logger.debug(outs)
		if errs:
			logger.error(errs)
			logger.error("Something went wrong running pandoc! Quitting...")
			logger.error("(Use -vv for more information)")
			sys.exit(2)

if __name__ == "__main__":
	pass
