
from lark import Transformer
from .util import get_path
import logging

logger = logging.getLogger('gams_injector')
logger.setLevel('DEBUG')
def get_id(item):
	if isinstance(item,str):
		return item
	elif item and 'id' in item:
		item_name=item['id']
	elif item and 'item' in item and 'id' in item['item']:
		item_name=item['item']['id']
	else:
		raise Exception("Unknown id format")
	return item_name

class TreeInject(Transformer):
	def __init__(self,context):
		self.context=context

	def start(self,args):
		logger.debug("Start")
		return "".join(args)

 	def statement(self,args):
		logger.debug('Statement')
		return "".join(args)

 	def white_space(self,args):
		logger.debug("White space")
		return args[0].value

 	def newline(self,args):
		return args[0].value

	def filter(self,args):
		logger.debug("Filter")
		def filter_fn(item):
			if args[1].data=='op_eq':
				return item[args[0]]==args[2]
			elif args[1].data=='op_sw':
				return item[args[0]].startswith(args[2])
			else:
				raise Exception("Unknown operator")
		return filter_fn

	def project(self,args):
		logger.debug("Project")
		items=[self.context['project']]
		return items

	def data(self,args):
		logger.debug("Data")
		items=self.context['data']
		return items

	def asset(self,args):
		logger.debug("Asset")
		items=self.context['asset']
		if len(args)>0:
			items=[i for i in items if args[0](i)]
		return items
		
	def item_exp(self,args):
		logger.debug("Item Expr")
		items=args[0]
		
		# If Children, filter
		if len(args)>1:
			filter_fn=args[1]
			items=[i for i in items if filter_fn(i)]

		return items

	def cmd_param(self,args):
		logger.debug("cmd Param")
		items=args[0]
		## ASSUME SELECTORS
		selector=args[1]
		if len(selector.children)>1:
			raise Exception("Only one selector allowed")
		selector=selector.children[0].strip("'")

		out_items=[]
		for item in items:
			logger.debug("Item")
			logger.debug("Selector {}".format(selector))
			if 'item' in item:
				value=get_path(item['item'],selector)
			else:
				value=get_path(item,selector)
			logger.debug("Value {}".format(value))

			if not value:
				continue

			if isinstance(value,float) or isinstance(value,int):
				out_items.append(item['item']['id']+" "+str(value))
			elif isinstance(value,dict):
				logger.debug("Value is a dictionary, nest values")
				for key in value:
					val=value[key]
					if isinstance(val,float) or isinstance(val,int):
						logger.debug("Adding {key}={val}".format(key=key,val=val))
						out_items.append(item['id']+'.'+key+" "+str(val))
					elif isinstance(val,str):
						logger.debug("Ignoring {key}={val}".format(key=key,val=val))
					else:
						logger.debug("Unknown {key}={val}".format(key=key,val=val))
			if isinstance(value,str):
				raise Exception("Parameters can not be strings")

		logger.debug("Out items {}".format(len(out_items)))
		return "{command}{args}".format(command="\n".join(out_items),args="".join(args[2:]))

	def cmd_map(self,args):
		logger.debug("cmd Map")
		project=args[0]
		## ASSSUME ONLY 1 PROJECT
		project_id=project[0]['id']
		items=args[1]

		out_items=[]
		for item in items:
			item_name=get_id(item)
			out_items.append(project_id+'.'+item_name)
		logger.debug("Out items {}".format(len(out_items)))
		return "{command}{args}".format(command="\n".join(out_items),args="".join(args[2:]))

	def cmd_list(self,args):
		logger.debug("cmd List")
		items=args[0]

		out_items=[]
		for item in items:
			item_name=get_id(item)
			out_items.append(item_name)
		return "{command}{args}".format(command=", ".join(out_items),args="".join(args[1:]))

 	def ao_macro(self,args):
		logger.debug("AO Macro - Inject Info")
		return "".join(args)
		#return "<-- AO {} - {} -->".format(command,", ".join(out_items))
