from QM_config_dynamic import QM_config, Circuit_info

the_specs = Circuit_info(q_num=2)
# print(the_specs.QsXyInfo)

''' Update the z info'''
z1 = the_specs.update_ZInfo_for(target_q='q1',con_channel=2,offset=-0.02,OFFbias=0.2,idle=0)
z2 = the_specs.update_ZInfo_for(target_q='q2',con_channel=4,offset=-0.035,OFFbias=0.13,idle=0.04)
print("After update the z info for q1 and q2 in spec:\n")
print(the_specs.ZInfo)

''' test update q1 waveform func to drag '''
the_specs.update_aXyInfo_for("q1",func='drag')
the_specs.update_aXyInfo_for("q2",func='gauss')
# print("\nUpdate q1 waveform func:\n")
# print(the_specs.QsXyInfo)

''' test update all the values for q1'''
the_specs.update_XyInfoS_for("q1",[0.2,20,4,-80,-0.5,-200,5])
the_specs.update_XyInfoS_for("q2",[0.14,20,4,120,-0.5,-200,5])
# print("\nUpdate q1 pi pulse info:\n")
# print(the_specs.QsXyInfo)

''' Update the T1 and T2 for q1 and q2 in the spec '''
the_specs.update_DecoInfo_for(target_q="q1",T1=10,T2=20)
the_specs.update_DecoInfo_for(target_q="q2",T1=13,T2=26)
print("\nAfter update the decoherence info for q1 and q2 in the spec:\n")
print(the_specs.DecoInfo)

init_config = QM_config()
print("initial config:\n")
print(init_config.get_config())

wiring = [
    {
        "name":"q1",
        "I":("con1", 1),
        "Q":("con1", 2),
        "mixer": "octave_octave1_1"
    },
    {
        "name":"q2",
        "I":("con1", 3),
        "Q":("con1", 4),
        "mixer": "octave_octave1_2"
    }
]
''' initialize the control parts in elements'''
x = the_specs.QsXyInfo
init_config.create_element_xy(wiring, x)
# print("\nAfter updating control elements:\n")
# print(init_config.get_config())

''' update the physical channels for control'''
init_config.update_control_channels("q1",I=("con2",5),Q=("con2",7))
init_config.update_control_mixer_correction("q2",(0.9,0.2,0.4,-0.9))
# print("\nAfter updating mixer corrections and channels:\n")
# print(init_config.get_config())

''' update LO and IF frequency '''
init_config.update_controlFreq(the_specs.update_aXyInfo_for("q2",LO=5.5,IF=2000))
# print(f"After update LO and IF for Q2:\n {init_config.get_config()['mixers']}")

''' update the amp and len '''
# print(f"Before update amp and len:\n {init_config.get_config()['waveforms']['minus_y90_Q_wf_q1']}")
the_specs.update_aXyInfo_for("q1",amp=0.34,len=33)
init_config.update_controlWaveform(the_specs.QsXyInfo)
# print(f"After update:\n{init_config.get_config()['waveforms']['minus_y90_Q_wf_q1']}")

''' update z bias '''
init_config.set_wiring("con1")
init_config.update_z_offset(Zinfo=z1,control_mache="con1",mode='idle')
init_config.update_z_offset(Zinfo=z2,control_mache="con1",mode='offset')
# print(f"After update the z offset:\n{init_config.get_config()}")

''' update the downconverter info '''
print(f"Before update:\n{init_config.get_config()['controllers']}")
init_config.update_downconverter(channel=1,offset=0.03,gain_db=3)
init_config.update_downconverter(channel=2,offset=0.027,gain_db=7)
print(f"\nAfter update:\n{init_config.get_config()['controllers']}")