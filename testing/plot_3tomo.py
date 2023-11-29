import numpy as np
import matplotlib.pyplot as plt
tomo_raw_data = np.load(r'testing/5Q_GHZ_5_4_3.npz', allow_pickle=True)# ["arr_0"].item()
# tomo_data =
for k, v in tomo_raw_data.items():
    print(k, v.shape)
# threshold = [2.007e-04, -5.748e-06, 1.421e-04]
threshold = [-5.748e-06, 2.007e-04, 1.421e-04]

q_names = ["rr5","rr4","rr3"]
q_order = [5,4,3]


tomo_data = {}

for q_o, q_name in zip(q_order, q_names):
    print(q_o, q_name, tomo_raw_data[q_name].shape)
    tomo_data[q_name] = np.moveaxis(tomo_raw_data[q_name],1,-1)[q_o*2-2:q_o*2]


bit_string = np.zeros(tomo_data[q_names[0]].shape[1:],dtype=int)

total_count = tomo_data[q_names[0]].shape[-1]
# plt.plot( r1_data[0][0][0],r1_data[1][0][0],'o')
# plt.show()
# plt.plot( r2_data[2][0][0],r2_data[3][0][0],'o')
# plt.show()

print( bit_string.shape )
for q_i, label in enumerate(q_names):
    q_address = len(q_names)-q_i-1
    print( label, 2**q_address, tomo_data[label].shape, threshold[q_address] )
    # ar_data = np.moveaxis(tomo_data[label],1,-1)
    bit_string += (tomo_data[label][0] > threshold[q_i]).astype(int)*(2**q_address)
    print(bit_string.shape)

probability_tomo = np.zeros(tomo_data[q_names[0]].shape[1:-1]+(2**len(q_names),))
print(probability_tomo.shape)
for i in range(3):
    ii = i-1
    if ii<0:
        ii=2
    for j in range(3):
        jj = j-1
        if jj<0:
            jj=2
        for k in range(3):
            kk = k-1
            if kk<0:
                kk=2
        # count_arr = np.unique(bit_string[i][j],return_counts=True)
            count_arr = np.bincount(bit_string[i][j][k])
            # print(count_arr, total_count, np.sum(count_arr))
            probability_tomo[ii][jj][kk] = count_arr/float(total_count)
print(probability_tomo.shape)


from scipy.io import savemat
savemat('3Q_tomo.mat',{"data":probability_tomo})
# x_mtx = np.matrix([[0,1],[1,0]])
# y_mtx = np.matrix([[0,-1j],[1j,0]])
# z_mtx = np.matrix([[1,0],[0,-1]])
# i_mtx = np.matrix([[1,0],[0,1]])
# S_ii = np.sum(probability_tomo[0][0])
# # S_ii = sum(list(probability_tomo[0][0].values()))

# # ### |00> for try
# S_xx = probability_tomo[1][1][0]-probability_tomo[1][1][1]-probability_tomo[1][1][2]+probability_tomo[1][1][3]
# S_xy = probability_tomo[1][2][0]-probability_tomo[1][2][1]-probability_tomo[1][2][2]+probability_tomo[1][2][3]
# S_xz = probability_tomo[1][0][0]-probability_tomo[1][0][1]-probability_tomo[1][0][2]+probability_tomo[1][0][3]
# S_yx = probability_tomo[2][1][0]-probability_tomo[2][1][1]-probability_tomo[2][1][2]+probability_tomo[2][1][3]
# S_yy = probability_tomo[2][2][0]-probability_tomo[2][2][1]-probability_tomo[2][2][2]+probability_tomo[2][2][3]
# S_yz = probability_tomo[2][0][0]-probability_tomo[2][0][1]-probability_tomo[2][0][2]+probability_tomo[2][0][3]
# S_zx = probability_tomo[0][1][0]-probability_tomo[0][1][1]-probability_tomo[0][1][2]+probability_tomo[0][1][3]
# S_zy = probability_tomo[0][2][0]-probability_tomo[0][2][1]-probability_tomo[0][2][2]+probability_tomo[0][2][3]
# S_zz = probability_tomo[0][0][0]-probability_tomo[0][0][1]-probability_tomo[0][0][2]+probability_tomo[0][0][3]
# S_ix = probability_tomo[1][1][0]-probability_tomo[1][1][1]+probability_tomo[1][1][2]-probability_tomo[1][1][3]
# S_iy = probability_tomo[2][2][0]-probability_tomo[2][2][1]+probability_tomo[2][2][2]-probability_tomo[2][2][3]
# S_iz = probability_tomo[0][0][0]-probability_tomo[0][0][1]+probability_tomo[0][0][2]-probability_tomo[0][0][3]
# S_xi = probability_tomo[1][1][0]+probability_tomo[1][1][1]-probability_tomo[1][1][2]-probability_tomo[1][1][3]
# S_yi = probability_tomo[2][2][0]+probability_tomo[2][2][1]-probability_tomo[2][2][2]-probability_tomo[2][2][3]
# S_zi = probability_tomo[0][0][0]+probability_tomo[0][0][1]-probability_tomo[0][0][2]-probability_tomo[0][0][3]

# RHO_mtx_gg_row1 = S_ii*np.kron(i_mtx,i_mtx)+S_ix*np.kron(i_mtx,x_mtx)+S_iy*np.kron(i_mtx,y_mtx)+S_iz*np.kron(i_mtx,z_mtx)
# RHO_mtx_gg_row2 = S_xi*np.kron(x_mtx,i_mtx)+S_xx*np.kron(x_mtx,x_mtx)+S_xy*np.kron(x_mtx,y_mtx)+S_xz*np.kron(x_mtx,z_mtx)
# RHO_mtx_gg_row3 = S_yi*np.kron(y_mtx,i_mtx)+S_yx*np.kron(y_mtx,x_mtx)+S_yy*np.kron(y_mtx,y_mtx)+S_yz*np.kron(y_mtx,z_mtx)
# RHO_mtx_gg_row4 = S_zi*np.kron(z_mtx,i_mtx)+S_zx*np.kron(z_mtx,x_mtx)+S_zy*np.kron(z_mtx,y_mtx)+S_zz*np.kron(z_mtx,z_mtx)

# DM_rho_gg = (RHO_mtx_gg_row1 + RHO_mtx_gg_row2 + RHO_mtx_gg_row3 + RHO_mtx_gg_row4)/4
# DM_gg_view = DM_rho_gg.view()
# imDM_gg_view = DM_rho_gg.imag.view()
# reDM_gg_view = DM_rho_gg.real.view()
# print(reDM_gg_view.shape)
# print("Prepare : ")
# print("Whole Density matrix: ")
# print(DM_gg_view)
# print("\nDensity matrix real part: ")
# print(reDM_gg_view)
# print("\nDensity matrix imaginary part: ")
# print(imDM_gg_view)
# print("Trace Rho: ",np.trace(DM_rho_gg))
# print("Trace Rho square: ",np.trace(np.square(DM_rho_gg)))

# print(type(DM_gg_view.A))
# from qutip.visualization import matrix_histogram_complex
# matrix_histogram_complex( DM_rho_gg.A )
# # fig, ax = plt.subplots(2,1)
# # # ax[0].imshow(reDM_gg_view)
# # # ax[1].imshow(imDM_gg_view)
# # c = ax[0].pcolormesh(reDM_gg_view, cmap='RdBu', vmin=-1, vmax=1)
# # ax[0].set_title('Re')
# # fig.colorbar(c, ax=ax[0])
# # c = ax[1].pcolormesh(imDM_gg_view, cmap='RdBu', vmin=-1, vmax=1)
# # ax[1].set_title('Im')
# # fig.colorbar(c, ax=ax[1])
# # fig.show()
# plt.show()