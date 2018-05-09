from distutils.core import setup
import py2exe

setup(
	windows=["test_run_script.py"],
	options={
		"py2exe":{
			"unbuffered": True,
			"optimize": 2,
			"excludes": ["email"]
		}
	}
)