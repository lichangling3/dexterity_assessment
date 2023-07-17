import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

'''Pipeline and helper functions'''

# --- DATA PREPARATION ---

""" Returns list of n by n elements of iterable. """
def grouped(iterable, n):
    return zip(*[iter(iterable)]*n)

""" Transform initial string data into list of 3D body points. """
def str2float(s):
    s = s.replace('[', '')
    s = s.replace(']', '')
    list = s.split(', ')
    list = [float(i) for i in list]

    new_list = np.zeros((17, 3))
    for (point, i) in zip(grouped(list, 4), range(17)):
        #We don't need the CI
        x = point[0]
        y = point[1]
        z = point[2]
        new_list[i] = np.array([x, y, z])
    return new_list

def get_df_points(data, col = 'kp3ds'):
    nbody_points = len(data[col][0])
    col_names = [f"point_{str(i)}" for i in range(nbody_points)]
    my_dict = {k: [] for k in col_names}

    for row in data[col]: 
        for (value, key) in zip(row, my_dict):
            my_dict[key].append(value)
    
    return pd.DataFrame(my_dict)

# --- HELPER FUNCTIONS ---

"""Returns the closest index for the wanted time period """
def time_id(data, t1, t2, col_name = 'time'):
    closest_index_1 = (data[col_name] - t1).abs().idxmin()
    closest_index_2 = (data[col_name] - t2).abs().idxmin()
    return [closest_index_1, closest_index_2]

# --- PLOT FUNCTIONS ---

""" Plot joint angles around 3 axis during a period of an event"""
def plot_angles(data, t1, t2, joint_name, event, x_vertical1 = None, x_vertical2 = None, label_vertical1=None, label_vertical2=None, vertical_line1 = False, vertical_line2 = False):
    idx = time_id(data, t1, t2)
    angles_x = [point[0] for point in data[joint_name][idx[0]:idx[1]]]
    angles_y = [point[1] for point in data[joint_name][idx[0]:idx[1]]]
    angles_z = [point[2] for point in data[joint_name][idx[0]:idx[1]]]
    time = data['time'][idx[0]:idx[1]]
    
    plt.figure(figsize=(12,5))
    if 'shoulder' in joint_name:
        plt.plot(time, angles_x, label = 'Rotation around x-axis (flexion)')
        plt.plot(time, angles_y, label = 'Rotation around y-axis')
        plt.plot(time, angles_z, label = 'Rotation around z-axis (abduction)')
    elif 'elbow' in joint_name:
        plt.plot(time, angles_x, label = 'Rotation around x-axis')
        plt.plot(time, angles_y, label = 'Rotation around y-axis')
        plt.plot(time, angles_z, label = 'Rotation around z-axis (flexion)')
    if 'trunk' in joint_name:
        plt.plot(time, angles_x, label = 'Rotation around x-axis (flexion)')
        plt.plot(time, angles_y, label = 'Rotation around y-axis')
        plt.plot(time, angles_z, label = 'Rotation around z-axis (lateral flexion)')

    if vertical_line1:
        plt.axvline(x_vertical1, label = label_vertical1, linestyle = '--', color = 'grey')

    if vertical_line2:
        plt.axvline(x_vertical2, label = label_vertical2, linestyle = '--', color = 'red')

    plt.gca().invert_yaxis()
    plt.title(f'{joint_name} when {event}')
    plt.xlabel('Time [s]')
    plt.ylabel('Angle [deg]')
    plt.legend()
    plt.show()

""" Plots all average joint velocities given a period of time in an event. """
def plot_joint_velocities(data, t1, t2, event, with_error = False):
    keys = [joint for joint in data.columns.values if 'angles' in joint]
    velocities_x = np.array([angle_velocity(data, t1, t2, name = key, axis = 0) for key in keys])
    velocities_y = np.array([angle_velocity(data, t1, t2, name = key, axis = 1) for key in keys])
    velocities_z = np.array([angle_velocity(data, t1, t2, name = key, axis = 2) for key in keys])
    plt.figure(figsize=(15,6))

    if with_error:
        plt.errorbar(x = keys, y = velocities_x[:,0], yerr = velocities_x[:,1], label = 'Rotation around x-axis', capsize = 5, fmt='o')
        plt.errorbar(x = keys, y = velocities_y[:,0], yerr = velocities_y[:,1], label = 'Rotation around y-axis', capsize=5, fmt = 'x')
        plt.errorbar(x = keys, y = velocities_z[:,0], yerr = velocities_z[:,1], label = 'Rotation around z-axis', capsize=5, fmt = 'v')
    else:
        plt.scatter(x = keys, y = velocities_x[:,0], label = 'Rotation around x-axis')
        plt.scatter(x = keys, y = velocities_y[:,0], label = 'Rotation around y-axis')
        plt.scatter(x = keys, y = velocities_z[:,0], label = 'Rotation around z-axis')

    plt.title(f'Average joint velocities when {event}')
    plt.ylabel('Average joint velocities [deg/s]')
    plt.legend()
    plt.show()

# --- INTERMEDIARY FEATURES ---

""" Returns the unit vector of the vector.  """
def unit_vector(vector):
    return vector / np.linalg.norm(vector)

""" Add naive joint angles to dataframe. """
def add_naive_joint_angles(data, parent_joint, joint, child_joint):
    v1 = data[parent_joint] - data[joint]
    v2 = data[child_joint] - data[joint]
    angles = []
    for v1_u, v2_u in zip(v1, v2):
        v1_u = unit_vector(v1_u)
        v2_u = unit_vector(v2_u)
        angle = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)) * 180 / np.pi
        angles.append(angle)
    data[joint+'_angle'] = angles

""" Returns mean angular velocity of angular velocities at each timestep
data = angles of joint of interest, t1 and t2 are expressed in seconds. """
def angle_velocity(data, t1, t2, name = 'leftelbow_angles', axis = 0):

    idx = time_id(data, t1, t2)
    angles = [point[axis] for point in data[name][idx[0]:idx[1]]]
    times = data['time'][idx[0]:idx[1]]
    sum = 0
    n = len(angles)
    w = []

    for i in range(n-1):
        w_i = np.abs((angles[i+1] - angles[i])/(times[i+1 + idx[0]] - times[i + idx[0]]))
        w.append(w_i)
    
    velocity = 1/n * np.sum(w)
    std = np.std(w)

    return (velocity, std)

""" Returns the distance of the total trajectory of one joint given a period of time"""
def dist_trajectory(data, t1, t2, joint_name):
    idx = time_id(data, t1, t2)
    points = data[joint_name][idx[0]:idx[1]]
    distance = 0
    dist_trajectory = 0
    n = len(points)

    for i in range(n-1):
        a = points[i + idx[0]]
        b = points[i+1 + idx[0]]
        distance = np.linalg.norm(b-a)
        dist_trajectory = dist_trajectory + distance

    return dist_trajectory


"""Returns the exact time.. ?"""
def time_trajectory(data, t1, t2): 
    idx = time_id(data, t1, t2)
    time = data['time'][idx[0]] - data['time'][idx[1]]

    return np.abs(time)

""" Returns the straight line distance between 2 points"""
def distance_AB(data, t1, t2, joint_name):
    idx = time_id(data, t1, t2)
    point_a = data[joint_name][idx[0]]
    point_b = data[joint_name][idx[1]]
    distance = np.linalg.norm(point_b - point_a)

    return distance

# --- FINAL FEATURES ---

""" Return the Range of Motion. """
def RoM(data, t1, t2, joint, axis = None): 
    idx = time_id(data, t1, t2)
    
    if axis == None:
        angles = data[joint][idx[0]:idx[1]]
    else: 
        angles = [value[axis] for value in data[joint][idx[0]:idx[1]]]
        
    max_angle = np.max(angles)
    min_angle = np.min(angles)
    RoM = max_angle - min_angle

    return RoM