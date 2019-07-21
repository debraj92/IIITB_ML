from rasa_core.channels import HttpInputChannel
from rasa_core.agent import Agent
from rasa_core.interpreter import RasaNLUInterpreter
from rasa_slack_connector import SlackInput


nlu_interpreter = RasaNLUInterpreter('./models/nlu/default/restaurantnlu')
agent = Agent.load('./models/dialogue', interpreter = nlu_interpreter)

input_channel = SlackInput('xoxp-523605566390-522098999251-521470971888-d5683dfbc5bc1e32153df531207634a8', #app verification token
							'xoxb-523605566390-521603579521-Iy0p23BzmZSSbKbBScAvnCj3', # bot verification token
							'FZFY8tyWnfEH4iP7A2EadE1z', # slack verification token
							True)

agent.handle_channel(HttpInputChannel(5003, '/', input_channel))