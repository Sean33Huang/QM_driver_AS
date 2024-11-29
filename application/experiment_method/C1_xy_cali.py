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
from exp.SQGate_calibration_new import SQGate_calibration
my_exp = SQGate_calibration(config, qmm)
my_exp.initializer = initializer(200000,mode='wait')
my_exp.ro_elements = ['q3_ro']
my_exp.xy_elements = ["q3_xy"]
my_exp.sequence_repeat = 1

# Are variables if process = 'amp'
my_exp.amp_ratio = 1

# Are variables if process = 'freq'
my_exp.virtial_detune_freq = 0.2
my_exp.point_per_period = 20
my_exp.max_period = 20

# Are variables if process = 'drag'
my_exp.draga_points = 150            

my_exp.process = 'freq'  # 'amp', 'freq', 'drag'

dataset = my_exp.run( 100 )

#Save data
save_data = True
folder_label = "xy_cali_freq_test"
if save_data: 
    from exp.save_data import DataPackager
    save_dir = link_config["path"]["output_root"]
    dp = DataPackager( save_dir, folder_label )
    dp.save_config(config)
    dp.save_nc(dataset,folder_label)

# Plot
save_figure = 1
from exp.plotting import PainterXYCali
painter = PainterXYCali()
painter.process = my_exp.process
figs = painter.plot(dataset,folder_label)
if save_figure: dp.save_figs( figs )
