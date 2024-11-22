from typing import Dict

class Analog_output:

    def __init__( self, channel_index:int ):
        """
        The analog_outputs part in controller
        """
        self._channel_index = channel_index
        self.offset = 0.0
        self.crosstalk = {}
        self.filter = {}

    def to_dict( self ):
        return {
            self._channel_index:{
                "offset":self.offset,
                "crosstalk":self.crosstalk,
                "filter":self.filter
            }
        }
class Filter:
    """ TODO """
    def __init__( self ):
        self.feedforward = []
        self.feedback = []


class Controller:
    def __init__(self, name:str ):
        """
        The controller part of configuration
        """
        self._name = name
        self._analog_outputs = {}
        self.digital_outputs =  {  # TODO
            1: {},
            3: {},
            5: {},
            7: {},
            10: {},
        }
        self.analog_inputs = {  # TODO
            1: {"offset": 0, "gain_db": 0},  # I from down-conversion
            2: {"offset": 0, "gain_db": 0},  # Q from down-conversion
        } 

    @property
    def name( self )->str:
        return self._name
        
    @property
    def analog_outputs( self )->Dict[int,Analog_output]:
        """ Analog output on hardware"""
        return self._analog_outputs
    @analog_outputs.setter
    def analog_outputs( self, val:Analog_output ):
        self._analog_outputs[val._channel_index] = val
    
    def to_dict( self ):

        analog_outputs = {}
        for k, v in self.analog_outputs.items():
            analog_outputs.update(v.to_dict())

        return {
            self._name:{
                "analog_outputs":analog_outputs,
                "digital_outputs": self.digital_outputs,
                "analog_inputs": self.analog_inputs,
            }
        }
    
    def add_analog_output( self, analog_output:Analog_output ):
        add_idx = analog_output._channel_index
        if add_idx not in self.analog_outputs.keys():
            self.analog_outputs[add_idx] = analog_output

def controller_read_dict( key:str, infos:dict )->Controller:
    """
    Input dictionary and output Controller object
    """
    new_controller = Controller(key)
    analog_outputs = infos["analog_outputs"]
    for k, infos in analog_outputs.items():
        channel_index = int(k)
        new_controller.analog_outputs[channel_index] = analog_output_read_dict( channel_index, infos )
    return new_controller

def analog_output_read_dict( channel_index:int, infos:dict )->Analog_output:
    """
    Input dictionary and output Analog_output object
    """
    analog_output = Analog_output( channel_index )
    analog_output.offset = infos["offset"]
    # analog_output.filter = infos["filter"]  TODO
    return analog_output
def controller_read_json( path ):
    pass

# def controller_read_pe
if __name__ == '__main__':
    new_controller = Controller("con1")
    for i in range(5):
        new_analog_output = Analog_output(i)
        new_controller.add_analog_output(new_analog_output)