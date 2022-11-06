import numpy as np
from copy import deepcopy as copy_deepcopy
from scipy.fft import dct, idct

# Notes about SSIM
# Good embedding quality SSIM >= 0.995
# Destroied images SSIM <= 0.9

class Embedder():
    def __init__(self):
        self.spots_to_swap = [[(2, 6), (3, 5)], [(5, 3), (6, 2)], [(0, 7), (7, 0)]]
        self.boost = 50
    

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
        

    def load_mark(self, mark):
        if type(mark) != type(str()):
            error = 'Error : mark has to be a string'
            return {'status' : False, 'error' : error}
        if len(mark) == 0:
            error = 'Error : mark length equal to zero'
            return {'status' : False, 'error' : error}
        self.mark = mark
        self.mark_size = len(mark)
        self.mark_partitioning = [325, 650]
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
        attributes = ['image', 'image_type', 'mark', 'mark_size', 'mark_partitioning']
        for attribute in attributes:
            if not hasattr(self, attribute):
                error = 'Error: missing ' + attribute + ' attribute'
                return {'status' : False, 'error' : error}
        return {'status' : True}
    

    def _check_parameters(self, layers_to_embed):
        try:
            # Remove bad input
            for layer in list(layers_to_embed):
                if layer != 'red' and layer != 'green' and layer != 'blue' and layer != 'grey':
                    layers_to_embed.remove(layer)
            # Grey image with more than one layer or with the layer name not equal to grey
            if len(self.image.shape) == 2 and len(layers_to_embed) != 1 and layers_to_embed[0] != 'grey':
                error = 'Invalid parameters: Grey scale image has only grey layer'
                return {'status' : False, 'error' : error}
            # No layers selected
            if len(layers_to_embed) == 0:
                error = 'Error: select atleast one layer'
                return {'status' : False, 'error' : error}
            # Rgb image with grey layer
            if len(self.image.shape) == 3 and self.image.shape[2] == 3 and ('grey' in layers_to_embed):
                error = 'Invalid parameters: Rgb images have no grey layer'
                return {'status' : False, 'error' : error}
            return {'status' : True}     
        except Exception as error:
            return {'status' : False, 'error' : str(error)}

    
    def _extract_layers(self, layers_to_embed):
        try:
            if len(layers_to_embed) == 0:
                error = 'Error: no layers to extract'
                return {'status' : False, 'error' : error}
            if self.image_type == 'grey':
                self.layers = {}
                grey_image = copy_deepcopy(self.image)
                self.layers['grey'] = grey_image
            elif self.image_type == 'rgb':
                self.layers = {}
                if 'red' in layers_to_embed:
                    red_image = copy_deepcopy(self.image)
                    self.layers['red'] = red_image[:, :, 0]
                if 'green' in layers_to_embed:
                    green_image = copy_deepcopy(self.image)
                    self.layers['green'] = green_image[:, :, 1]
                if 'blue' in layers_to_embed:
                    blue_image = copy_deepcopy(self.image)
                    self.layers['blue'] = blue_image[:, :, 2]
            else:
                error = 'Error: invalid image type'
                return {'status' : False, 'error' : error}
            return {'status' : True}
        except Exception as error:
            del self.layers
            return {'status' : False, 'error' : str(error)}
    

    def _calculate_mark_per_layer(self, layers_to_embed):
        if len(layers_to_embed) == 0:
            error = 'Error: Division by zero -> len(layers_to_embed) = 0'
            return {'status' : False, 'error' : error}
        self.mark_per_layer = self.mark_size / len(layers_to_embed)
        self.remainder = 0
        if type(self.mark_per_layer) == type(float()):
            self.mark_per_layer = round(self.mark_per_layer)
            self.remainder = self.mark_size - (self.mark_per_layer * len(layers_to_embed))
        return {'status' : True}
    

    def _create_watermarked_image(self):
        try:
            self.watermarked_image = copy_deepcopy(self.image)
            if self.image_type == 'grey':
                self.watermarked_image = self.layers['grey']
            elif self.image_type == 'rgb':
                for layer in self.layers:
                    if layer == 'red':
                        self.watermarked_image[:, :, 0] = self.layers[layer]
                    elif layer == 'green':
                        self.watermarked_image[:, :, 1] = self.layers[layer]
                    elif layer == 'blue':
                        self.watermarked_image[:, :, 2] = self.layers[layer]
            else:
                del self.watermarked_image
                error = 'Error: invalid image type'
                return {'status' : False, 'error' : error}
            return {'status' : True}
        except Exception as error:
            del self.watermarked_image
            return {'status' : False, 'error' : str(error)}


    def embed(self, layers_to_embed, embed_rateo):
        # Calculate chunk size
        results = self._calculate_chunk_size(embed_rateo)
        if not results['status']:
            return results
        # Check if attributes exists
        results = self._check_attributes()
        if not results['status']:
            return results
        # Check if parameters are correct
        results = self._check_parameters(layers_to_embed)
        if not results['status']:
            return results
        # Extract the layers from the image
        results = self._extract_layers(layers_to_embed)
        if not results['status']:
            return results
        # Calculate the mark portion that has to be inserted in each channel
        results = self._calculate_mark_per_layer(layers_to_embed)
        if not results['status']:
            return results
        # Embed cicle
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
            # Insert each bit of the mark into a chunk
            try:
                portion_index = 0
                for i in range(self.mark_per_layer):
                    # Select the right spot where to insert the bit
                    if (i + mark_index) >= self.mark_partitioning[0] and (i + mark_index) < self.mark_partitioning[1]:
                        portion_index = 1
                    elif (i + mark_index) >= self.mark_partitioning[1]:
                        portion_index = 2
                    # Apply the DCT to the chunk
                    chunk = self.layers[layer][chunks[(i + mark_index) * offset][0] : chunks[(i + mark_index) * offset][1], chunks[(i + mark_index) * offset][2] : chunks[(i + mark_index) * offset][3]]
                    chunk_dct = dct(dct(chunk, axis = 0, norm = 'ortho'), axis = 1, norm = 'ortho')
                    # Check the difference between the two spots
                    spots_difference = abs(chunk_dct[self.spots_to_swap[portion_index][0]] - chunk_dct[self.spots_to_swap[portion_index][1]])
                    # If we want to embed 0 boost the first spot, else boost the second one
                    chunk_dct[self.spots_to_swap[portion_index][int(self.mark[(i + mark_index)])]] = (chunk_dct[self.spots_to_swap[portion_index][int(self.mark[(i + mark_index)])]]) + spots_difference + self.boost
                    # Apply the IDCT to the chunk
                    chunk_idct = np.rint(idct(idct(chunk_dct, axis = 1, norm = 'ortho'), axis = 0, norm = 'ortho'))
                    if np.max(chunk_idct) > 255 or np.min(chunk_idct) < 0:
                        chunk_idct = np.clip(chunk_idct, 0, 255)  
                    self.layers[layer][chunks[(i + mark_index) * offset][0] : chunks[(i + mark_index) * offset][1], chunks[(i + mark_index) * offset][2] : chunks[(i + mark_index) * offset][3]] = chunk_idct
            except Exception as error:
                return {'status' : False, 'error' : str(error)}
            # Update mark index
            mark_index += self.mark_per_layer
        # Create watermarked image
        results = self._create_watermarked_image()
        return results
        