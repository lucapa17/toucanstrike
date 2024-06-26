import argparse
import importlib.util
import os

from secml_malware.models import CClassifierEnd2EndMalware, MalConv, CClassifierRemote

from constants import *
from prompts import error_prompt, success_prompt, crash_prompt
from state import global_state


def get_target_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument('target',
						help='target for the attacks. Examples already implemented: malconv, gbdt_ember, sorel_dnn, remote')
	parser.add_argument('--model_path',
						help='path to the weights of the model. Leave empty for MalConv to load default weights embedded in library.')
	parser.add_argument('--antivirus',
						help='antivirus service. Choose either virustotal or metadefender.'\
          				'Leave empty if you are targeting a remote antivirus by URL')
	parser.add_argument('--antivirus_url',
						help='antivirus URL. Specify the URL of the remote antivirus classifier'\
          				'Leave empty if you are targeting virustotal or metadefender')
	parser.add_argument('--apikey',
						help='authentication token for your service.'\
						'Leave empty according to service requested.'\
          				'If you have multiple API keys, you can specify them separated by commas. For example: apikey1,apikey2,apikey3')
	return parser


def target(args):
	if args.target is None:
		error_prompt('You have to set a target.')
		error_prompt(f'Chose one from this list: {ALL_MODELS}')

		return

	if args.target == MALCONV:
		clf = CClassifierEnd2EndMalware(model=MalConv())
		if args.model_path is None:
			clf.load_pretrained_model()
		else:
			clf.load_pretrained_model(args.model_path)
		_set_target(clf)
		return

	if args.target == REMOTE:
		clf = CClassifierRemote(args.antivirus_url, args.antivirus, args.apikey.split(",") if args.apikey is not None else None)
		_set_target(clf)
		return

	if not os.path.isdir(global_state.plugin_path):
		crash_prompt(f"The plugin path {global_state.plugin_path} does not exists!")
		return

	plugins = os.listdir(global_state.plugin_path)
	if args.target not in plugins:
		error_prompt(f"The target {args.target} does not exists among the plugins.")
		return

	try:
		module = importlib.import_module(f'plugins.{args.target}.model')
		clf = module.load_model(args.model_path)
		_set_target(clf)
		return
	except Exception as e:
		crash_prompt(f"Can't import plugin {args.target}")
		crash_prompt(f"Error was: {e}")
		return


def _set_target(clf):
	global_state.target = clf
	success_prompt('Target set!')
