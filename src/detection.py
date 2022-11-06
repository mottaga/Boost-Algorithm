import numpy as np
from scipy.fft import dct
from functools import reduce
from operator import mul as operator_mul
from generate_new_mark import accuracy
from copy import deepcopy as copy_deepcopy

# Combinations calculator
def ncr(n, r):
    try:
        r = min(r, n-r)
        numer = reduce(operator_mul, range(n, n-r, -1), 1)
        denom = reduce(operator_mul, range(1, r+1), 1)
        return {'status' : True, 'result' : numer // denom}
    except Exception as error:
        return {'status' : False, 'error' : str(error)}


def identify(mark_extracted, marks):
    accuracies = []
    try:
        first_candidate = {'accuracy' : -1, 'index' : -1}
        second_candidate = {'accuracy' : -1, 'index' : -1}
        last_candidate = {'accuracy' : None, 'index' : -1}
        for i in range(len(marks)):
            result = accuracy(mark_extracted, marks[i])
            if result['status']:
                acc = result['result']
                accuracies.append(acc)
                if (acc >= first_candidate['accuracy']):
                    second_candidate = copy_deepcopy(first_candidate)
                    first_candidate['accuracy'] = acc
                    first_candidate['index'] = i
                elif (acc >= second_candidate['accuracy']):
                    second_candidate['accuracy'] = acc
                    second_candidate['index'] = i
                if ((last_candidate['accuracy'] == None) or (acc <= last_candidate['accuracy'])):
                    last_candidate['accuracy'] = acc
                    last_candidate['index'] = i
        print(f"Accuracies: {accuracies}") # debug print
        average_with_no_first = [accuracies[i] for i in range(len(accuracies)) if i != first_candidate['index']]
        average_with_no_first = sum(average_with_no_first) / len(average_with_no_first)
        average_with_no_first_and_last = [accuracies[i] for i in range(len(accuracies)) if (i != first_candidate['index']) and (i != last_candidate['index']) ]
        average_with_no_first_and_last = sum(average_with_no_first_and_last) / len(average_with_no_first_and_last)
        difference_lower = abs(last_candidate['accuracy'] - 40)
        difference_upper = abs(first_candidate['accuracy'] - 53.59)
        # Embedded and attacked - upper bound
        if((last_candidate['accuracy'] < 40) and difference_lower > difference_upper):
            return {'status': True, 'index': last_candidate['index'], 'accuracy': 100 - last_candidate['accuracy'], 'attacked' : True, 'accuracies' : accuracies}
        # Embedded but not attacked
        elif(first_candidate['accuracy'] > 97):
            return {'status': True, 'index': first_candidate['index'], 'accuracy': first_candidate['accuracy'], 'attacked' : False, 'accuracies' : accuracies}
        elif((first_candidate['accuracy'] >= 53.59) and (first_candidate['accuracy'] <= 97) and (difference_upper > difference_lower)):            
            return {'status': True, 'index': first_candidate['index'], 'accuracy': first_candidate['accuracy'], 'attacked' : True, 'accuracies' : accuracies}
        # Not embedded
        else:
            return {'status': True, 'index': -1, 'accuracy': first_candidate['accuracy'], 'attacked' : None, 'accuracies' : accuracies} 
    except Exception as error:
        return {'status': False, 'error': error}


class Analyzer():
    def __init__(self):
        pass
    

    def load_image(self, image):
        try:
            if image.shape[2] == 1:
                self.image_type = 'grey'
                self.image = image
            elif image.shape[2] == 3:
                self.image_type = 'rgb'
                self.image = image
            else:
                error = 'Error: Image shape not supported'
                return {'status' : False, 'error' : error}
            return {'status' : True}    
        except Exception as error:
            return {'status' : False, 'error' : str(error)}
    

    def set_attributes(self, mark_size, mark_partitioning, spots_to_swap, embed_rateo):
        # Check if we have loaded the image
        if not hasattr(self, 'image'):
            error = 'Error: load the image before setting the attributes'
            return {'status' : False, 'error' : error}
        # Check the mark size
        if mark_size < 0:
            error = 'Error: mark size < 0'
            return {'status' : False, 'error' : error}
        self.mark_size = mark_size
        # Check the mark partitioning
        if type(mark_partitioning) != type(list()):
            error = 'Error : mark partitioning has to be a list'
            return {'status' : False, 'error' : error}
        for elem in mark_partitioning:
            if type(elem) != type(int()):
                error = 'Error: mark partitioning cant contains not integer elements'
                return {'status' : False, 'error' : error}
            elif type(elem) == type(int()) and elem < 0:
                error = 'Error: mark partitioning cant contains negative numbers'
                return {'status' : False, 'error' : error}
        self.mark_partitioning = mark_partitioning
        # Calculate chunk size
        results = self._calculate_chunk_size(embed_rateo)
        if not results['status']:
            return results
        # Check the spots to swap
        if type(spots_to_swap) != type(list(list())):
            error = 'Error: spots_to_swap has to be a list of lists'
            return {'status' : False, 'error' : error}
        for elem in spots_to_swap:
            for sub_elem in elem:
                if type(sub_elem) != type(list()) and type(sub_elem) != type(tuple()):
                    error = 'Error: spots_to_swap has to be a list of lists with tuple or lists insides'
                    return {'status' : False, 'error' : error}
                for i in range(len(sub_elem)):
                    if type(sub_elem[i]) != type(int()):
                        error = 'Error: spots_to_swap has to be a list of lists with tuple / lists of integers'
                        return {'status' : False, 'error' : error}
                    if ((type(sub_elem[i]) == type(int())) and (sub_elem[i] < 0 or sub_elem[i] > self.chunk_size[i])):
                        error = 'Error: negative number in spots to swap or value exced chunk_size'
                        return {'status' : False, 'error' : error}
        self.spots_to_swap = spots_to_swap
        return {'status' : True}


    def _calculate_chunk_size(self, embed_rateo):
        # Check if image is loaded
        if not hasattr(self, 'image'):
            error = 'self has not image attribute'
            return {'status' : False, 'error' : error}
        x = self.image.shape[0]
        y = self.image.shape[1]
        # Calculate x, y factors
        x_factors = []
        y_factors = []
        for i in range(1, x + 1):
            if x % i == 0:
                x_factors.append(i)
        for i in range(1, y + 1):
            if y % i == 0:
                y_factors.append(i)
        # Search the best factor
        total_pixels = x * y
        best_resolution = {'resolution' : None, 'distance' : None}
        for i in range(len(x_factors)):
            for j in range(len(y_factors)):
                if (x_factors[i] >= 8 and y_factors[j] >= 8):
                    total_chunks = total_pixels / (x_factors[i] * y_factors[j])
                    if total_chunks >= self.mark_size * embed_rateo:
                        if ((best_resolution['distance'] is None) or (abs(x_factors[i] - y_factors[j]) <= best_resolution['distance'])):
                            best_resolution['resolution'] = (x_factors[i], y_factors[j])
                            best_resolution['distance'] = abs(x_factors[i] - y_factors[j])
        if best_resolution['resolution'] is not None:
            self.chunk_size = best_resolution['resolution']
            return {'status' : True}
        else:
            error = 'Chunk size not found'
            return {'status' : False, 'error' : error}


    def _check_attributes(self):
        attributes = ['image', 'image_type', 'mark_size', 'mark_partitioning', 'chunk_size', 'spots_to_swap']
        for attribute in attributes:
            if not hasattr(self, attribute):
                error = 'Error: missing ' + attribute + ' attribute'
                return {'status' : False, 'error' : error}
        return {'status' : True}
    

    def _check_parameters(self, layers_embedded):
        try:
            # Remove bad input
            for layer in list(layers_embedded):
                if layer != 'red' and layer != 'green' and layer != 'blue' and layer != 'grey':
                    layers_embedded.remove(layer)
            # Grey image with more than one layer or with the layer name not equal to grey
            if len(self.image.shape) == 2 and len(layers_embedded) != 1 and layers_embedded[0] != 'grey':
                error = 'Invalid parameters: Grey scale image has only grey layer'
                return {'status' : False, 'error' : error}
            # No layers selected
            if len(layers_embedded) == 0:
                error = 'Error: select atleast one layer'
                return {'status' : False, 'error' : error}
            # Rgb image with grey layer
            if len(self.image.shape) == 3 and self.image.shape[2] == 3 and ('grey' in layers_embedded):
                error = 'Invalid parameters: Rgb images have no grey layer'
                return {'status' : False, 'error' : error}
            return {'status' : True}     
        except Exception as error:
            return {'status' : False, 'error' : str(error)}
    

    def _extract_layers(self, layers_embedded):
        try:
            if len(layers_embedded) == 0:
                error = 'Error: no layers to extract'
                return {'status' : False, 'error' : error}
            if self.image_type == 'grey':
                self.layers = {}
                grey_image = copy_deepcopy(self.image)
                self.layers['grey'] = grey_image
            elif self.image_type == 'rgb':
                self.layers = {}
                if 'red' in layers_embedded:
                    red_image = copy_deepcopy(self.image)
                    self.layers['red'] = red_image[:, :, 0]
                if 'green' in layers_embedded:
                    green_image = copy_deepcopy(self.image)
                    self.layers['green'] = green_image[:, :, 1]
                if 'blue' in layers_embedded:
                    blue_image = copy_deepcopy(self.image)
                    self.layers['blue'] = blue_image[:, :, 2]
            else:
                error = 'Error: invalid image type'
                return {'status' : False, 'error' : error}
            return {'status' : True}
        except Exception as error:
            del self.layers
            return {'status' : False, 'error' : str(error)}
    

    def _calculate_mark_per_layer(self, layers_embedded):
        if len(layers_embedded) == 0:
            error = 'Error: Division by zero -> len(layers_embedded) = 0'
            return {'status' : False, 'error' : error}
        self.mark_per_layer = self.mark_size / len(layers_embedded)
        self.remainder = 0
        if type(self.mark_per_layer) == type(float()):
            self.mark_per_layer = round(self.mark_per_layer)
            self.remainder = self.mark_size - (self.mark_per_layer * len(layers_embedded))
        return {'status' : True}
    

    def detect(self, layers_embedded):
        # Check if attributes exists
        results = self._check_attributes()
        if not results['status']:
            return results
        # Check if parameters are correct
        results = self._check_parameters(layers_embedded)
        if not results['status']:
            return results
        # Extract the layers from the image
        results = self._extract_layers(layers_embedded)
        if not results['status']:
            return results
        # Calculate the mark portion that has to be inserted in each channel
        results = self._calculate_mark_per_layer(layers_embedded)
        if not results['status']:
            return results
        # Detect cicle
        self.mark_extracted = ''
        layer_number = 0
        mark_index = 0
        for layer in self.layers:
            # Update layer_number
            layer_number += 1
            # Check if it is the last layer to be embedded
            if (layer_number == len(self.layers)) and (self.remainder != 0):
                self.mark_per_layer += self.remainder
            # Calculate the embedding offset between each bit of the mark
            try:
                total_chunks = (self.image.shape[0] * self.image.shape[1]) // (self.chunk_size[0] * self.chunk_size[1])
                modulo_rest = total_chunks % self.mark_size
                offset = (total_chunks - modulo_rest) // self.mark_size
            except Exception as error:
                return {'status' : False, 'error' : str(error)}
            # Walk the layer chunk by chunk
            try:
                chunks = []
                for i in range(0, self.image.shape[0], self.chunk_size[0]):
                    for j in range(0, self.image.shape[1], self.chunk_size[1]):
                        coordinates = (i, i + self.chunk_size[0], j, j + self.chunk_size[1])
                        chunks.append(coordinates)
            except Exception as error:
                return {'status' : False, 'error' : str(error)}
            # Extract one bit from each chunk
            try:
                portion_index = 0
                for i in range(self.mark_per_layer):
                    # Select the right spot where to extract the bit
                    if (i + mark_index) >= self.mark_partitioning[0] and (i + mark_index) < self.mark_partitioning[1]:
                        portion_index = 1
                    elif (i + mark_index) >= self.mark_partitioning[1]:
                        portion_index = 2
                    # Apply the DCT to the chunk
                    chunk = self.layers[layer][chunks[(i + mark_index) * offset][0] : chunks[(i + mark_index)* offset][1], chunks[(i + mark_index) * offset][2] : chunks[(i + mark_index) * offset][3]]
                    chunk_dct = dct(dct(chunk, axis = 0, norm = 'ortho'), axis = 1, norm = 'ortho')
                    # Check where is the max value, if the max value is in the first spot is a zero, else is a one
                    if (chunk_dct[self.spots_to_swap[portion_index][0]] > chunk_dct[self.spots_to_swap[portion_index][1]]):
                        self.mark_extracted += '0'
                    else:
                        self.mark_extracted += '1'
            except Exception as error:
                del self.mark_extracted
                return {'status' : False, 'error' : str(error)}
            # Update mark_index
            mark_index += self.mark_per_layer
        return {'status' : True}