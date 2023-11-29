from QM_config_dynamic import QM_config, Circuit_info
from qualang_tools.units import unit

u = unit(coerce_to_integer=True)

myConfig = QM_config()
the_spec = Circuit_info(q_num=4)
choose = 0


if choose == 0:
    # Update z 
    z1 = the_spec.update_ZInfo_for(target_q='q1',controller='con1',con_channel=5,offset=0,OFFbias=0.016,idle=0)
    z2 = the_spec.update_ZInfo_for(target_q='q2',controller='con1',con_channel=6,offset=0,OFFbias=-0.141,idle=0)
    z3 = the_spec.update_ZInfo_for(target_q='q3',controller='con1',con_channel=9,offset=0.211,OFFbias=0,idle=0.1431)
    z4 = the_spec.update_ZInfo_for(target_q='q4',controller='con1',con_channel=10,offset=0.217,OFFbias=0,idle=0)



    # Update the xy 
    the_spec.update_aXyInfo_for("q1",func='gauss')
    the_spec.update_aXyInfo_for("q2",func='gauss')
    the_spec.update_aXyInfo_for("q3",func='gauss')
    the_spec.update_aXyInfo_for("q4",func='gauss')

    # Update the T1 and T2 for q1 and q2 in the spec 
    # the_spec.update_DecoInfo_for(target_q="q1",T1=5,T2=3)
    # the_spec.update_DecoInfo_for(target_q="q2",T1=5,T2=3)

    # Update XY info
    the_spec.update_XyInfoS_for("q1",[0.046,40,3.955-0.201-0.072,-80+34.7+24.1+13.6-2.31,0,-200,0])
    the_spec.update_XyInfoS_for("q2",[0.0575,40,4.385,-80-15.1+24.1-1,0,-200,0])
    the_spec.update_XyInfoS_for("q3",[0.046,40,3.955-0.201-0.072,-80+34.7+24.1+13.6-2.31,0,-200,0])
    the_spec.update_XyInfoS_for("q4",[0.0575,40,4.385,-80-15.1+24.1-1,0,-200,0])

    # Update RO info
    the_spec.update_RoInfo_for("q1",LO=5.9,IF= -158.112,amp=0.006,time=288,len=2000)
    the_spec.update_RoInfo_for("q2",IF= 129.397,amp=0.0095)
    the_spec.update_RoInfo_for("q3",IF= -45.468,amp=0.015)
    the_spec.update_RoInfo_for("q4",IF= 225.425,amp=0.012)

    # Update the wiring info
    the_spec.update_WireInfo_for("q1",ro_mixer='octave_octave1_1',xy_mixer='octave_octave1_2',up_I=("con1", 1),up_Q=("con1", 2),down_I=("con1", 1),down_Q=("con1", 2),xy_I=("con1", 3),xy_Q=("con1", 4))
    the_spec.update_WireInfo_for("q2",ro_mixer='octave_octave1_1',xy_mixer='octave_octave1_4',up_I=("con1", 1),up_Q=("con1", 2),down_I=("con1", 1),down_Q=("con1", 2),xy_I=("con1", 7),xy_Q=("con1", 8))
    the_spec.update_WireInfo_for("q3",ro_mixer='octave_octave1_1',xy_mixer='octave_octave1_3',up_I=("con1", 1),up_Q=("con1", 2),down_I=("con1", 1),down_Q=("con1", 2),xy_I=("con1", 3),xy_Q=("con1", 4))
    the_spec.update_WireInfo_for("q4",ro_mixer='octave_octave1_1',xy_mixer='octave_octave1_5',up_I=("con1", 1),up_Q=("con1", 2),down_I=("con1", 1),down_Q=("con1", 2),xy_I=("con1", 7),xy_Q=("con1", 8))

    myConfig.set_wiring("con1")

    myConfig.update_z_offset(Zinfo=z1,mode='OFFbias')
    myConfig.update_z_offset(Zinfo=z2,mode='OFFbias')
    myConfig.update_z_offset(Zinfo=z3,mode='idle')
    myConfig.update_z_offset(Zinfo=z4,mode='offset')

    myConfig.create_qubit("q1",the_spec.RoInfo,the_spec.XyInfo,the_spec.WireInfo)
    myConfig.create_qubit("q2",the_spec.RoInfo,the_spec.XyInfo,the_spec.WireInfo)
    myConfig.create_qubit("q3",the_spec.RoInfo,the_spec.XyInfo,the_spec.WireInfo)
    myConfig.create_qubit("q4",the_spec.RoInfo,the_spec.XyInfo,the_spec.WireInfo)

    myConfig.update_downconverter(channel=1,offset= 0.0156584060058594, gain_db= 0)
    myConfig.update_downconverter(channel=2,offset= 0.00627351550292969, gain_db= 0)

    the_spec.export_spec("Quantum-Control-Applications\Superconducting\Two-Flux-Tunable-Transmons\spec_v1115")
    myConfig.export_config("Quantum-Control-Applications\Superconducting\Two-Flux-Tunable-Transmons\config_v1115")

else:
    the_spec.import_spec("Quantum-Control-Applications\Superconducting\Two-Flux-Tunable-Transmons\spec_v1115")
    myConfig.import_config("Quantum-Control-Applications\Superconducting\Two-Flux-Tunable-Transmons\config_v1115")

    print(myConfig.get_config()['waveforms'])