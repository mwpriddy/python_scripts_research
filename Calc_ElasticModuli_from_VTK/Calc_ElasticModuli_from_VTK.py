#
# Calc_ElasticModuli_from_VTK.py
#
# Written by Matthew Priddy on March 1, 2015
# Some functions contributed by Noah Paulson
#
# Contact information:
# Matthew W. Priddy: 	mwpriddy (at) gatech (dot) edu 
#						mwpriddy (at) gmail (dot) com
# 
# The purpose of this code is to directional elastic moduli from stress/strain data
# calculated from FEM/MKS/etc.  
#
# The stress/strain data comes from uniaxial strain boundary conditions, but elastic moduli
# values are typically determined from unixial stress boundary conditions.
#
# Specifically, this code will:
# (1) volume average stress and strain components for loading in x-, y-, and z-directions
# (2) determine stiffness matrix (C_ij) components
# (3) invert stiffness matrix to determine compliance matrix (S_ij)
# (4) calculate elastic moduli for x-, y-, and z-direction
# 
# Notes: (a) you must use decimals to return decimals
#		 (b) sin, cos, etc. use Radians
#
from sys import *
from string import *
from math import *
from numpy import *
import vtk

# Read in (or, in this case, assign) the file prefix and material names
#fileName = sys.argv[1]
#material = sys.argv[2]

fileName = "mks_alphaTi"
material = "random"

# Some VTK functions that might be used in this script
def VTK_Header(fileName, file_input, nx_pt, ny_pt, nz_pt, X, Y, Z, no_el):
	fileName.write("# vtk DataFile Version 2.0"																		"\n")
	fileName.write("data file: " + file_input + " generated by Matthew W. Priddy on " +str(time.strftime("%c")) + 	"\n")
	fileName.write("ASCII" + 													 									"\n")
	fileName.write("DATASET RECTILINEAR_GRID" + 								 									"\n")
	fileName.write("DIMENSIONS " + str(nx_pt) + " " + str(ny_pt) + " " + str(nz_pt) +								"\n")
	fileName.write("X_COORDINATES " + str(nx_pt) + " float"						 									"\n")
	for i in range(len(X)):
		fileName.write("% 2.4f " %(X[i])																				)
		if i == len(X):
			fileName.write("\n"																							)
	fileName.write("\n"																									)
	fileName.write("Y_COORDINATES " + str(ny_pt) + " float"						 									"\n")
	for i in range(len(Y)):
		fileName.write("% 2.4f " %(Y[i])																				)
		if i == len(Y):
			fileName.write("\n"																							)
	fileName.write("\n"																									)
	fileName.write("Z_COORDINATES " + str(nz_pt) + " float"						 									"\n")
	for i in range(len(Z)):
		fileName.write("% 2.4f " %(Z[i])																				)
		if i == len(Z):
			fileName.write("\n"																							)
	fileName.write("\n"																									)	

	fileName.write("CELL_DATA " + str(no_el) +									 									"\n")

def VTK_Scalar(fileName, dataName, data, no_per_line):
	fileName.write("SCALARS " + dataName + " float " + str(1) +					 									"\n")
	fileName.write("LOOKUP_TABLE default" 										 									"\n")
	for i in range(len(data)):
		fileName.write("% 2.6E " %(data[i])																				)
		i = i + 1
		if i % no_per_line == 0:
			fileName.write("\n"																							)
		elif i == len(data):
			fileName.write("\n"																							)
			
def VTK_Scalar_Int(fileName, dataName, data, no_per_line):
	fileName.write("SCALARS " + dataName + " int " + str(1) +					 									"\n")
	fileName.write("LOOKUP_TABLE default" 										 									"\n")
	for i in range(len(data)):
		fileName.write("% 5d " %(data[i])																				)
		i = i + 1
		if i % no_per_line == 0:
			fileName.write("\n"																							)	
		elif i == len(data):
			fileName.write("\n"																							)
			
def VTK_Vector(fileName, dataName, data, no_per_line):
	fileName.write("VECTORS " + dataName + " float " +							 									"\n")
	for i in range(len(data[0,:])):
		fileName.write(" % +2.6E % +2.6E % +2.6E    " %(data[0,i], data[1,i], data[2,i])								)
		i = i + 1
		if i % no_per_line == 0:
			fileName.write("\n"																							)
		elif i == len(data[0,:]):
			fileName.write("\n"																							)
		
def VTK_Tensor(fileName, dataName, data_00, data_01, data_02, data_11, data_12, data_22, no_per_line):
	fileName.write("TENSORS " + dataName + " float " +								 								"\n")
	for i in range(len(data_00)):
		fileName.write(" % +2.6E % +2.6E % +2.6E % +2.6E % +2.6E % +2.6E % +2.6E % +2.6E % +2.6E " 
			%(data_00[i], data_01[i], data_02[i], data_01[i], data_11[i], data_12[i], data_02[i], data_12[i], data_22[i]) + "\n" )

def read_vtk_tensor(filename, tensor_id, comp):
    """
    Summary:
        Much of this code was taken from Matthew Priddy's example file.
    Inputs:
    Outputs:
    """

    # Initialize the reading of the VTK microstructure created by Dream3D
    reader = vtk.vtkDataSetReader()
    reader.SetFileName(filename)
    reader.ReadAllTensorsOn()
    reader.ReadAllVectorsOn()
    reader.ReadAllScalarsOn()
    reader.Update()
    data = reader.GetOutput()
    dim = data.GetDimensions()
    vec = list(dim)
    vec = [i-1 for i in dim]

    el = vec[0]

    # Calculate the total number of elements
    el_total = el**3

    if tensor_id == 0:
        # if meas == 0, we read the stress tensor
        meas = data.GetCellData().GetArray(reader.GetTensorsNameInFile(0))
    elif tensor_id == 1:
        # if meas == 1, we read the strain tensor
        meas = data.GetCellData().GetArray(reader.GetTensorsNameInFile(1))
    elif tensor_id == 2:
        # if meas == 2, we read the plastic strain tensor
        meas = data.GetCellData().GetArray(reader.GetTensorsNameInFile(2))

    meas_py = zeros([el_total])

    for ii in xrange(el_total):
        meas_py[ii] = meas.GetValue(ii*9 + comp)

    return meas_py

def read_vtk_vector(filename):
    """
    Summary:
        Much of this code was taken from Matthew Priddy's example file.
    Inputs:
    Outputs:
    """

    # Initialize the reading of the VTK microstructure created by Dream3D
    reader = vtk.vtkDataSetReader()
    reader.SetFileName(filename)
    reader.ReadAllTensorsOn()
    reader.ReadAllVectorsOn()
    reader.ReadAllScalarsOn()
    reader.Update()
    data = reader.GetOutput()
    dim = data.GetDimensions()
    vec = list(dim)
    vec = [i-1 for i in dim]

    el = vec[0]

    # Calculate the total number of elements
    el_total = el**3

    Euler = data.GetCellData().GetArray(reader.GetVectorsNameInFile(0))

    euler_py = zeros([3, el_total])

    for ii in xrange(el_total):
        euler_py[0, ii] = Euler.GetValue(ii*3 + 0)
        euler_py[1, ii] = Euler.GetValue(ii*3 + 1)
        euler_py[2, ii] = Euler.GetValue(ii*3 + 2)

    return euler_py

def read_vtk_scalar(filename):
    """
    Summary:
        Much of this code was taken from Matthew Priddy's example file.
    Inputs:
    Outputs:
    """

    # Initialize the reading of the VTK microstructure created by Dream3D
    reader = vtk.vtkDataSetReader()
    reader.SetFileName(filename)
    reader.ReadAllTensorsOn()
    reader.ReadAllVectorsOn()
    reader.ReadAllScalarsOn()
    reader.Update()
    data = reader.GetOutput()
    dim = data.GetDimensions()
    vec = list(dim)
    vec = [i-1 for i in dim]

    el = vec[0]

    # Calculate the total number of elements
    el_total = el**3

    Scalar = data.GetCellData().GetArray(reader.GetScalarsNameInFile(0))

    scalar_py = zeros([el_total])

    for ii in xrange(el_total):
        scalar_py[ii] = Scalar.GetValue(ii)

    return scalar_py

###### Start of actual Code ######

# Initialize the average stress and strain tensors
stress_avg_xdir = zeros((3,3))
stress_avg_ydir = zeros((3,3))
stress_avg_zdir = zeros((3,3))

strain_avg_xdir = zeros((3,3))
strain_avg_ydir = zeros((3,3))
strain_avg_zdir = zeros((3,3))

# Iterate over the (a) number of simulations, (b) number of cycles, and (c) three loading directions
for num_simulations in range(0,1):
	print "Simulation: " + str(num_simulations + 1)
	
	for cycles in range(0,1):
		cycles = cycles + 1
		print "  Cycle: " + str(cycles)
		
		for num_directions in range(0,3):
			print "    Direction: " + str(num_directions + 1)

			if num_directions == 0:
				f1_all = fileName + '_Xdir_IDval_' + material + '_sn' + str(num_simulations) + '_step' + str(2*cycles - 1) + '.vtk'
			
			elif num_directions == 1:
				f1_all = fileName + '_Ydir_IDval_' + material + '_sn' + str(num_simulations) + '_step' + str(2*cycles - 1) + '.vtk'

			elif num_directions == 2:
				f1_all = fileName + '_Zdir_IDval_' + material + '_sn' + str(num_simulations) + '_step' + str(2*cycles - 1) + '.vtk'

			# Initialize the reading of the VTK file
			reader = vtk.vtkDataSetReader()
			reader.SetFileName(f1_all)
			reader.ReadAllTensorsOn()
			reader.ReadAllVectorsOn()
			reader.ReadAllScalarsOn()
			reader.Update()
			data = reader.GetOutput()
			dim = data.GetDimensions()
			vec = list(dim)
			vec = [i-1 for i in dim]

			elements = vec[0]*vec[0]*vec[0]

		# Preallocate stress and strain components
			elemID_max   = [0.0 for i in range(elements)]
			strs_t00_max = [0.0 for i in range(elements)] 
			strs_t11_max = [0.0 for i in range(elements)] 
			strs_t22_max = [0.0 for i in range(elements)]
			strs_t01_max = [0.0 for i in range(elements)] 
			strs_t02_max = [0.0 for i in range(elements)] 
			strs_t12_max = [0.0 for i in range(elements)]
			strn_t00_max = [0.0 for i in range(elements)]
			strn_t11_max = [0.0 for i in range(elements)]
			strn_t22_max = [0.0 for i in range(elements)]
			strn_t01_max = [0.0 for i in range(elements)]
			strn_t02_max = [0.0 for i in range(elements)]
			strn_t12_max = [0.0 for i in range(elements)]

		# (1) Extract stress and strain for all elements in VTK file
		# f1 is the initial max loading (tyically in tension)
			strs_t00_max = read_vtk_tensor(f1_all, 0, 0)
			strs_t11_max = read_vtk_tensor(f1_all, 0, 4)
			strs_t22_max = read_vtk_tensor(f1_all, 0, 8)
			strs_t01_max = read_vtk_tensor(f1_all, 0, 1)
			strs_t02_max = read_vtk_tensor(f1_all, 0, 2)
			strs_t12_max = read_vtk_tensor(f1_all, 0, 5)
			
			strn_t00_max = read_vtk_tensor(f1_all, 1, 0)
			strn_t11_max = read_vtk_tensor(f1_all, 1, 4)
			strn_t22_max = read_vtk_tensor(f1_all, 1, 8)
			strn_t01_max = read_vtk_tensor(f1_all, 1, 1)
			strn_t02_max = read_vtk_tensor(f1_all, 1, 2)
			strn_t12_max = read_vtk_tensor(f1_all, 1, 3)

		# Average the normal stress and strain values in order to determine the elastic moduli for each loading direction
			if num_directions == 0:
				stress_avg_xdir[0,0] = sum(strs_t00_max) / len(strs_t00_max)
				stress_avg_xdir[1,1] = sum(strs_t11_max) / len(strs_t11_max)
				stress_avg_xdir[2,2] = sum(strs_t22_max) / len(strs_t22_max)

				strain_avg_xdir[0,0] = sum(strn_t00_max) / len(strn_t00_max)
				strain_avg_xdir[1,1] = sum(strn_t11_max) / len(strn_t11_max)
				strain_avg_xdir[2,2] = sum(strn_t22_max) / len(strn_t22_max)
				
		#		stress_avg_xdir[0,1] = sum(strs_t01_max) / len(strs_t01_max)
		#		stress_avg_xdir[0,2] = sum(strs_t02_max) / len(strs_t02_max)
		#		stress_avg_xdir[1,0] = sum(strs_t01_max) / len(strs_t01_max)
		#		stress_avg_xdir[1,2] = sum(strs_t12_max) / len(strs_t12_max)
		#		stress_avg_xdir[2,0] = sum(strs_t02_max) / len(strs_t02_max)
		#		stress_avg_xdir[2,1] = sum(strs_t12_max) / len(strs_t12_max)

		#		strain_avg_xdir[0,1] = sum(strn_t01_max) / len(strn_t01_max)
		#		strain_avg_xdir[0,2] = sum(strn_t02_max) / len(strn_t02_max)
		#		strain_avg_xdir[1,0] = sum(strn_t01_max) / len(strn_t01_max)
		#		strain_avg_xdir[1,2] = sum(strn_t12_max) / len(strn_t12_max)
		#		strain_avg_xdir[2,0] = sum(strn_t02_max) / len(strn_t02_max)
		#		strain_avg_xdir[2,1] = sum(strn_t12_max) / len(strn_t12_max)
				
			elif num_directions == 1:
				stress_avg_ydir[0,0] = sum(strs_t00_max) / len(strs_t00_max)
				stress_avg_ydir[1,1] = sum(strs_t11_max) / len(strs_t11_max)
				stress_avg_ydir[2,2] = sum(strs_t22_max) / len(strs_t22_max)

				strain_avg_ydir[0,0] = sum(strn_t00_max) / len(strn_t00_max)
				strain_avg_ydir[1,1] = sum(strn_t11_max) / len(strn_t11_max)
				strain_avg_ydir[2,2] = sum(strn_t22_max) / len(strn_t22_max)
				
			elif num_directions == 2:
				stress_avg_zdir[0,0] = sum(strs_t00_max) / len(strs_t00_max)
				stress_avg_zdir[1,1] = sum(strs_t11_max) / len(strs_t11_max)
				stress_avg_zdir[2,2] = sum(strs_t22_max) / len(strs_t22_max)

				strain_avg_zdir[0,0] = sum(strn_t00_max) / len(strn_t00_max)
				strain_avg_zdir[1,1] = sum(strn_t11_max) / len(strn_t11_max)
				strain_avg_zdir[2,2] = sum(strn_t22_max) / len(strn_t22_max)

		# Determine elastic moduli from averaged data
		C_matrix = array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
		S_matrix = array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])

		# Define C_ij
		C_matrix[0,0] = stress_avg_xdir[0,0] / strain_avg_xdir[0,0]
		C_matrix[0,1] = stress_avg_xdir[1,1] / strain_avg_xdir[0,0]
		C_matrix[0,2] = stress_avg_xdir[2,2] / strain_avg_xdir[0,0]
		C_matrix[1,0] = stress_avg_ydir[0,0] / strain_avg_ydir[1,1]
		C_matrix[1,1] = stress_avg_ydir[1,1] / strain_avg_ydir[1,1]
		C_matrix[1,2] = stress_avg_ydir[2,2] / strain_avg_ydir[1,1]
		C_matrix[2,0] = stress_avg_zdir[0,0] / strain_avg_zdir[2,2]
		C_matrix[2,1] = stress_avg_zdir[1,1] / strain_avg_zdir[2,2]
		C_matrix[2,2] = stress_avg_zdir[2,2] / strain_avg_zdir[2,2]
#		print C_matrix

		# Invert C_ij to determine S_ij
		S_matrix = linalg.inv(C_matrix)

		# print each of the elastic moduli
		print "    X-direction: E_11 = " + str(1.0/S_matrix[0,0])
		print "    Y-direction: E_22 = " + str(1.0/S_matrix[1,1])
		print "    Z-direction: E_33 = " + str(1.0/S_matrix[2,2])