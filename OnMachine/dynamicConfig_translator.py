
from QM_config_dynamic import QM_config, Circuit_info
from qualang_tools.units import unit
from numpy import pi

u = unit(coerce_to_integer=True)

myConfig = QM_config()
the_spec = Circuit_info(q_num=5)
choose = 0

# initialize the dynamic configuration
if choose == 0: 
    # Update z 
    z1 = the_spec.update_ZInfo_for(target_q='q1',controller='con1',con_channel=5,offset=-0.039,OFFbias=0.1,idle=-0.299)
    z2 = the_spec.update_ZInfo_for(target_q='q2',controller='con1',con_channel=6,offset=-0.059,OFFbias=0.2,idle=-0.059)
    z3 = the_spec.update_ZInfo_for(target_q='q3',controller='con1',con_channel=9,offset=-0.04,OFFbias=0.16,idle=0.16)
    z4 = the_spec.update_ZInfo_for(target_q='q4',controller='con1',con_channel=10,offset=-0.039,OFFbias=0.2,idle=-0.039)
   

    # Update the xy 
    the_spec.update_aXyInfo_for("q1",func='drag',amp=0.102,len=24,LO=3.500 + 0.38,IF=-92.85,draga=0.55,delta=-(450.2-344.2)*2,AC=0,half=1)
    the_spec.update_aXyInfo_for("q2",func='drag',amp=0.1054,len=24,LO=3.900 + 0.43,IF=-85.02,draga=0.2,delta=(470.7-369.2)*2,AC=0,half=1)
    the_spec.update_aXyInfo_for("q3",func='drag',amp=0.173,len=24,LO=3.300 + 0.08,IF=-146.6,draga=2.1,delta=200,AC=0,half=1)
    the_spec.update_aXyInfo_for("q4",func='drag',amp=0.175,len=24,LO=3.200,IF=372.9,draga=0,delta=200,AC=0,half=1)

    # Update the T1 and T2 for q1 and q2 in the spec (if needed)
    the_spec.update_DecoInfo_for(target_q="q1",T1=25,T2=15)
    # the_spec.update_DecoInfo_for(target_q="q2",T1=5,T2=3)


    # Update RO info
    the_spec.update_RoInfo_for("q1",LO=5.96,IF=-237.55-0.05,amp=0.018*1.3,time=280,len=1200, ge_hold=-1.421e-03, rotated=((18.7+251.9-6.4)/180)*pi)
    the_spec.update_RoInfo_for("q2",LO=5.96,IF= 54.44,amp=0.020*1.2, ge_hold=3.893e-04, rotated=( (41.5-0.5) / 180) * pi)
    the_spec.update_RoInfo_for("q3",LO=5.96,IF= (-123.85-0.8),amp=0.020*1.2, ge_hold=8.577e-5, rotated=((287.2+300+236) / 180) * pi)
    the_spec.update_RoInfo_for("q4",LO=5.96,IF= (142.54),amp=0.02, ge_hold=4.641e-5, rotated=(31.7 / 180) * pi)

    # Update the wiring info
    the_spec.update_WireInfo_for("q1",ro_mixer='octave_octave1_1',xy_mixer='octave_octave1_2',up_I=("con1", 1),up_Q=("con1", 2),down_I=("con1", 1),down_Q=("con1", 2),xy_I=("con1", 3),xy_Q=("con1", 4))
    the_spec.update_WireInfo_for("q2",ro_mixer='octave_octave1_1',xy_mixer='octave_octave1_3',up_I=("con1", 1),up_Q=("con1", 2),down_I=("con1", 1),down_Q=("con1", 2),xy_I=("con1", 7),xy_Q=("con1", 8))
    the_spec.update_WireInfo_for("q3",ro_mixer='octave_octave1_1',xy_mixer='octave_octave1_4',up_I=("con1", 1),up_Q=("con1", 2),down_I=("con1", 1),down_Q=("con1", 2),xy_I=("con1", 3),xy_Q=("con1", 4))
    the_spec.update_WireInfo_for("q4",ro_mixer='octave_octave1_1',xy_mixer='octave_octave1_5',up_I=("con1", 1),up_Q=("con1", 2),down_I=("con1", 1),down_Q=("con1", 2),xy_I=("con1", 7),xy_Q=("con1", 8))

    # Inntialize the controller
    myConfig.set_wiring("con1")

    # Update the z bias into the controller
    myConfig.update_z_offset(Zinfo=z1,mode='offset')
    myConfig.update_z_offset(Zinfo=z2,mode='offset')
    myConfig.update_z_offset(Zinfo=z3,mode='offset')
    myConfig.update_z_offset(Zinfo=z4,mode='offset')

    # Create the XY and RO channels for a qubit
    myConfig.create_qubit("q1",the_spec.get_spec_forConfig('ro'),the_spec.get_spec_forConfig('xy'),the_spec.get_spec_forConfig('wire'))
    myConfig.create_qubit("q2",the_spec.get_spec_forConfig('ro'),the_spec.get_spec_forConfig('xy'),the_spec.get_spec_forConfig('wire'))
    myConfig.create_qubit("q3",the_spec.get_spec_forConfig('ro'),the_spec.get_spec_forConfig('xy'),the_spec.get_spec_forConfig('wire'))
    myConfig.create_qubit("q4",the_spec.get_spec_forConfig('ro'),the_spec.get_spec_forConfig('xy'),the_spec.get_spec_forConfig('wire'))

    # update RO integration weights
    myConfig.update_integrationWeight(target_q='q1',updated_RO_spec=the_spec.get_spec_forConfig('ro'),from_which_value='rotated')
    myConfig.update_integrationWeight(target_q='q2',updated_RO_spec=the_spec.get_spec_forConfig('ro'),from_which_value='rotated')
    myConfig.update_integrationWeight(target_q='q3',updated_RO_spec=the_spec.get_spec_forConfig('ro'),from_which_value='rotated')
    myConfig.update_integrationWeight(target_q='q4',updated_RO_spec=the_spec.get_spec_forConfig('ro'),from_which_value='rotated')

    # update the downconvertion in the controller
    myConfig.update_downconverter(channel=1,offset= 0.006487780227661133+0.00832853277297247, gain_db= 0)
    myConfig.update_downconverter(channel=2,offset= 0.004683707580566406+0.008599453735351563, gain_db= 0)

    the_spec.export_spec(r'/Users/ratiswu/Documents/GitHub/QM_opt/OnMachine/Spec_Alloffset_1208')
    myConfig.export_config(r'/Users/ratiswu/Documents/GitHub/QM_opt/OnMachine/Config_Alloffset_1208')

# else:
    # the_spec.import_spec("TESTspec_1201")
    # myConfig.import_config("TESTconfig_1201")

    # print(myConfig.get_config()['pulses'])
    ### for some useful update

    # Update the controll mixer corections
    myConfig.update_mixer_correction(target_q='q1',correct=(0.995,0.002,0.015,0.989),mode='xy')

    # Update the control frequency like IF or LO
    # myConfig.update_controlFreq(the_spec.update_aXyInfo_for("q2",LO=5.5,IF=2000))

    # Update the pi pulse amp or len...
    # the_spec.update_aXyInfo_for("q1",amp=0.34,len=33)
    # myConfig.update_controlWaveform(target_q='q1',updatedSpec=the_spec.get_spec_forConfig('xy'))

    # Update the RO frequency
    # myConfig.update_ReadoutFreqs(the_spec.update_RoInfo_for(target_q='q2',IF=280))
    # myConfig.update_ReadoutFreqs(the_spec.update_RoInfo_for(target_q='q2',LO=7))

    # Update the RO amp or others
    # the_spec.update_RoInfo_for(target_q='q2',amp=0.01,ge_hold=0.02)
    # the_spec.update_RoInfo_for(target_q='q1',rotated=0.087)
    # the_spec.update_RoInfo_for(target_q='anyQ',len=2500,time=700)
    # myConfig.update_Readout(target_q='q1',RoInfo=the_spec.get_spec_forConfig('ro'),integration_weights_from='rotated')
    
    # Update the RO mixer corections
    # myConfig.update_mixer_correction(target_q='q2',correct=(0.995,0.002,0.015,0.989),mode='ro')

    # Update the RO wiring channels
    # myConfig.update_wiring_channels(target_q="q1",mode="ro",I=("con1",100),Q=("con1",999))

    #print(the_spec.get_ReadableSpec_fromQ("q2",'xy'))
    # print(myConfig.get_config()['elements'])

