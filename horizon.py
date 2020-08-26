#!/usr/local/bin/python3

from PIL import Image
from numpy import *
from scipy.ndimage import filters
import sys
import imageio
from functools import reduce
import operator

# calculate "Edge strength map" of an image
#
def edge_strength(input_image):
    grayscale = array(input_image.convert('L'))
    filtered_y = zeros(grayscale.shape)
    filters.sobel(grayscale,0,filtered_y)
    return sqrt(filtered_y**2)

# draw a "line" on an image (actually just plot the given y-coordinates
#  for each x-coordinate)
# - image is the image to draw on
# - y_coordinates is a list, containing the y-coordinates and length equal to the x dimension size
#   of the image
# - color is a (red, green, blue) color triple (e.g. (255, 0, 0) would be pure red
# - thickness is thickness of line in pixels
#
def draw_edge(image, y_coordinates, color, thickness):
    for (x, y) in enumerate(y_coordinates):
        for t in range( int(max(y-int(thickness/2), 0)), int(min(y+int(thickness/2), image.size[1]-1 )) ):
            image.putpixel((x, t), color)
    return image

# main program
#
(input_filename, gt_row, gt_col) = sys.argv[1:]

# load in image 
input_image = Image.open(input_filename)

# compute edge strength mask
edge_strength = edge_strength(input_image)
imageio.imwrite('edges.jpg', uint8(255 * edge_strength / (amax(edge_strength))))

############
## Simple Solution ##
############

def simple():
    ridge = [argmax(edge_strength[:,i]) for i in range(edge_strength.shape[1])] # max value from each column
    imageio.imwrite("output_simple.jpg", draw_edge(input_image, ridge, (0, 0, 255), 5))

###################
## Using Viterbi ##
###################

def viterbi_map():
    def emission(state, col):
        curr_column = edge_strength[:,col]
        curr_state = curr_column[state]
        prob = curr_state/sum(curr_column)
        if prob > .005:
            return prob*99
        return prob

    def transition(old_state, new_state):
        diff = abs(old_state - new_state)
        if diff == 0:
            return .4
        if diff == 1:
            return .3
        if diff == 2:
            return .2
        if diff == 3:
            return .05
        if diff == 4:
            return .04

        else:
            return .000001

    img_height = edge_strength.shape[0] # 141 in mountain.jpg
    img_width = edge_strength.shape[1] # 251 in mountain.jpg
    states = range(img_height)

    viterbi = zeros((img_width+1, img_height+1))
    back_pointers = zeros((img_width, img_height+1))

    for state in states:
        viterbi[0][state] = emission(state, 0) #col 0
        back_pointers[0][state] = 0

    for col in range(1, img_width):
        for state in states:

            for tmp_state in states:
                tmp = viterbi[col-1][tmp_state] * transition(tmp_state, state)

                if tmp>viterbi[col][state]:
                    viterbi[col][state] = tmp
                    back_pointers[col][state] = tmp_state
            viterbi[col][state] *= emission(state, col)

    t_max = -1
    vit_max = -1
    for state in states:
        if viterbi[img_width-1][state] > vit_max:
            t_max = state
            vit_max = viterbi[img_width-1][state]

    def backtrack(img_width, t):
        i = img_width
        tags = [0 for i in range(img_width+1)]
        while(i>0):
            tags[i] = t
            t = int(back_pointers[i][t])
            i -= 1

        return tags

    ridge = backtrack(img_width-1, t_max)
    imageio.imwrite("output_map.jpg", draw_edge(input_image, ridge, (255, 0, 0), 5))
    return ridge


def human_influenced():
# initial set up
    img_height = edge_strength.shape[0] # 141 in mountain.jpg
    img_width= edge_strength.shape[1] # 251 in mountain.jpg

    # TODO: configure transition, emission and initial probabilities
    #  so that they are not garbage

    # might want to construct matrices instead of having
    # functions for the transition and emissions probs instead

    # helper function for transition probabilities
    # P(S_i+1=s_i+1|S_i+s_i+1)
    total = (img_height / 2)**2
    def transition(old_state, new_state):
        diff = abs(old_state - new_state)
        if diff == 0:
            return .4
        if diff == 1:
            return .3
        if diff == 2:
            return .2
        if diff == 3:
            return .05
        if diff == 4:
            return .04

        else:
            return .0001

    # helper function for the emissions probabilities
    # P(W_i=w_i|S_i=s_i)
    def emission(state, col):
        if state == int(gt_row) and col == int(gt_col):
            return 10000000000
        curr_column = edge_strength[:,col]
        curr_state = curr_column[state]
        prob = curr_state/sum(curr_column)
        if prob > .005:
            return prob*99
        return prob

    columns = [edge_strength[:,i] for i in range(img_width)]

    first_max_index = max(range(img_height), key=lambda i: edge_strength[0][i])
    initial = [transition(first_max_index, i) for i in range(img_height)]

    ## Viterbi Algorithm
    T1 = [[0 for t in range(img_width)] for k in range(img_height)]
    T2 = [[0 for t in range(img_width)] for k in range(img_height)]
    for i in range(1, img_height):
            T1[i][0] = initial[i] * emission(i, 0)
            T2[i][0] = None

    for j in range(1, img_width):
        for i in range(img_height):
            T1[i][j] = max([T1[k][j-1] * transition(k, i) for k in range(img_height)]) * emission(i, j)
            T2[i][j] = max(range(img_height), key=lambda k: T1[k][j-1] * transition(k, i))

    ridge = [0 for t in range(img_width)]
    ridge[img_width - 1] = max(range(img_height), key=lambda k: T1[k][img_width - 1])
    for j in range(img_width - 1, 1, -1): ridge[j-1] = T2[ridge[j]][j]
    
    #print(ridge, "\n\n", T1, "\n\n", T2)

    imageio.imwrite("output_human.jpg", draw_edge(input_image, ridge, (0, 255, 0), 5))

#simple() 
viterbi_map()
#human_influenced()
