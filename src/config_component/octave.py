from typing import Dict

class RF_output:
    def __init__( self, channel_index:int ):
        """
        The RF_outputs part in octave
        """
        self._channel_index = channel_index
        self.LO_frequency = ()
        self.LO_source = "internal"
        self.output_mode = "always_on"
        self.gain = ()

    def to_dict( self ):
        return {
            self._channel_index:{
                "LO_frequency": self.LO_frequency,
                "LO_source": self.LO_source,
                "output_mode": self.output_mode,
                "gain": self.gain
            }
        }

class RF_input:
    def __init__( self, channel_index:int ):
        """
        The RF_inputs part in octave
        """
        self._channel_index = channel_index
        self.LO_frequency = ()
        self.LO_source = "internal"
        self.IF_mode_I = "direct"
        self.IF_mode_Q = "direct"

    def to_dict( self ):
        return {
            self._channel_index:{
                "LO_frequency": self.LO_frequency,
                "LO_source": self.LO_source,
                "IF_mode_I": self.IF_mode_I,
                "IF_mode_Q": self.IF_mode_Q,
            }
        }    


class Octave:
    def __init__(self, name:str ):
        """
        The octave part of configuration
        """
        self._name = name
        self._RF_outputs = {}
        self._RF_inputs = {}
        self._connectivity = "con1"


    @property
    def name( self )->str:
        return self._name
        
    @property
    def RF_outputs( self )->Dict[int,RF_output]:
        """ RF output on hardware"""
        return self._RF_outputs
    @RF_outputs.setter
    def RF_outputs( self, val:RF_output ):
        self._RF_outputs[val._channel_index] = val
    
    @property
    def RF_inputs( self )->Dict[int,RF_input]:
        """ RF input on hardware"""
        return self._RF_inputs
    @RF_inputs.setter
    def RF_inputs( self, val:RF_input ):
        self._RF_inputs[val._channel_index] = val

    def to_dict( self ):
        RF_outputs = {}
        for k, v in self.RF_outputs.items():
            RF_outputs.update(v.to_dict())
        RF_inputs = {}
        for k, v in self.RF_inputs.items():
            RF_inputs.update(v.to_dict())
        return {
            self._name:{
                "RF_outputs": RF_outputs,
                "RF_inputs": RF_inputs,
                "connectivity": self._connectivity,
            }
        }
    
    def add_RF_output( self, RF_output:RF_output ):
        add_idx = RF_output._channel_index
        if add_idx not in self.RF_outputs.keys():
            self.RF_outputs[add_idx] = RF_output

    def add_RF_input( self, RF_input:RF_input ):
        add_idx = RF_input._channel_index
        if add_idx not in self.RF_inputs.keys():
            self.RF_inputs[add_idx] = RF_input

def octave_read_dict( key:str, infos:dict )->Octave:
    """
    Input dictionary and output Octave object
    """
    new_octave = Octave(key)
    RF_outputs = infos["RF_outputs"]
    RF_inputs = infos["RF_inputs"]

    for k, infos in RF_outputs.items():
        channel_index = int(k)
        new_octave.RF_outputs[channel_index] = RF_output_read_dict( channel_index, infos )
    for k, infos in RF_inputs.items():
        channel_index = int(k)
        new_octave.RF_inputs[channel_index] = RF_input_read_dict( channel_index, infos )
    return new_octave

def RF_output_read_dict( channel_index:int, infos:dict )->RF_output:
    """
    Input dictionary and output RF_output object
    """
    rf_output = RF_output( channel_index )
    rf_output.LO_frequency = infos["LO_frequency"]
    rf_output.gain = infos["gain"]
    return rf_output

def RF_input_read_dict( channel_index:int, infos:dict )->RF_input:
    """
    Input dictionary and output RF_input object
    """
    rf_input = RF_input( channel_index )
    rf_input.LO_frequency = infos["LO_frequency"]
    return rf_input
def octave_read_json( path ):
    pass

# def octave_read_pe
if __name__ == '__main__':
    new_octave = Octave("con1")
    for i in range(5):
        new_RF_output = RF_output(i)
        new_octave.add_RF_output(new_RF_output)

    print(new_octave.to_dict())