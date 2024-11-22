# Import necessary file
from pathlib import Path
link_path = Path(__file__).resolve().parent.parent/"config_api"/"config_link.toml"

from QM_driver_AS.ultitly.config_io import import_config, import_link
link_config = import_link(link_path)
config_obj, spec = import_config( link_path )

config = config_obj.get_config()
qmm, _ = spec.buildup_qmm()

from ab.QM_config_dynamic import initializer

# Set parameters
from exp.SQGate_amp_calibration import SQGate_amp_calibration
my_exp = SQGate_amp_calibration(config, qmm)
my_exp.initializer = initializer(10000,mode='wait')
my_exp.ro_elements = ['q3_ro']
my_exp.xy_elements = ["q3_xy"]
my_exp.amp_ratio = 1            # is variable if process = 'amp'
my_exp.sequence_repeat = 20     # is variable if process = 'repeat'
my_exp.freq_range = (-10, 10)   # is variable if process = 'freq'
my_exp.freq_resolution = 0.5    
my_exp.process = 'freq'  # 'amp', 'repeat', 'freq'
my_exp.gate = 1
dataset = my_exp.run( 200 )

#Save data
save_data = True
folder_label = "xy_amp_cali"
if save_data: 
    from exp.save_data import DataPackager
    save_dir = link_config["path"]["output_root"]
    dp = DataPackager( save_dir, folder_label )
    dp.save_config(config)
    dp.save_nc(dataset,folder_label)

# Plot
save_figure = 1
from exp.plotting import PainterXYCaliAmp
painter = PainterXYCaliAmp()
painter.process = my_exp.process
painter.gate = my_exp.gate
figs = painter.plot(dataset,folder_label)
if save_figure: dp.save_figs( figs )
